from decimal import Decimal
from html import escape

import stripe
from django.conf import settings
from rest_framework import serializers

from notifications.tasks import send_telegram_notification
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

FINE_MULTIPLIER = Decimal("2")


def to_cents(amount):
    return int(amount * 100)


def _get_frontend_url(request):
    """In dev frontend runs on port 5173, in prod same origin."""
    host = request.get_host()
    if ":8000" in host:
        host = host.replace(":8000", ":5173")
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{host}"


def create_stripe_session(borrowing, request):
    if Payment.objects.filter(borrowing=borrowing, type=Payment.Type.PAYMENT).exists():
        raise serializers.ValidationError(
            "A payment for this borrowing already exists."
        )
    frontend_url = _get_frontend_url(request)
    days = (borrowing.expected_return_date - borrowing.borrow_date).days
    total_price = borrowing.book.daily_fee * days
    amount_in_cents = to_cents(total_price)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{borrowing.book.title} — {days} days borrowing",
                    },
                    "unit_amount": amount_in_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        metadata={"borrowing_id": str(borrowing.id), "type": Payment.Type.PAYMENT},
        success_url=frontend_url + "/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=frontend_url + "/payments/cancel",
    )

    Payment.objects.create(
        borrowing=borrowing,
        status=Payment.Status.PENDING,
        type=Payment.Type.PAYMENT,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=total_price,
    )


def create_fine_session(borrowing, request):

    if borrowing.actual_return_date is None:
        raise serializers.ValidationError(
            "Cannot create a fine for an active borrowing"
        )
    if Payment.objects.filter(borrowing=borrowing, type=Payment.Type.FINE).exists():
        raise serializers.ValidationError("A fine for this borrowing already exists.")

    days_overdue = (borrowing.actual_return_date - borrowing.expected_return_date).days
    if days_overdue <= 0:
        raise serializers.ValidationError(
            "Borrowing was returned on time, no fine is due."
        )

    frontend_url = _get_frontend_url(request)
    fine_amount = borrowing.book.daily_fee * days_overdue * FINE_MULTIPLIER
    amount_in_cents = to_cents(fine_amount)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{borrowing.book.title} — {days_overdue} days overdue fine",
                    },
                    "unit_amount": amount_in_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        metadata={"borrowing_id": str(borrowing.id), "type": Payment.Type.FINE},
        success_url=frontend_url + "/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=frontend_url + "/payments/cancel",
    )

    Payment.objects.create(
        borrowing=borrowing,
        status=Payment.Status.PENDING,
        type=Payment.Type.FINE,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=fine_amount,
    )


def mark_payment_paid(payment):
    """Atomic PENDING -> PAID switch: only the call that actually changes
    the status sends the notification (the success page and the webhook can
    both fire, and Stripe may redeliver events)."""
    switched = Payment.objects.filter(
        pk=payment.pk, status=Payment.Status.PENDING
    ).update(status=Payment.Status.PAID)
    payment.status = Payment.Status.PAID
    if switched:
        send_telegram_notification.delay(
            f"💰 <b>Payment Successful</b>\n"
            f"Type: {payment.type}\n"
            f"Amount: ${payment.money_to_pay}\n"
            f"User: {escape(payment.borrowing.user.email)}\n"
            f"Book: {escape(payment.borrowing.book.title)}"
        )
    return switched


def session_matches_payment(payment, session):
    metadata = session["metadata"]
    expected = {"borrowing_id": str(payment.borrowing_id), "type": payment.type}
    return (
        session["amount_total"] == to_cents(payment.money_to_pay)
        and session["currency"] == "usd"
        and all(k in metadata and metadata[k] == v for k, v in expected.items())
    )
