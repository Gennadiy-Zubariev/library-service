from decimal import Decimal

import stripe
from django.conf import settings

from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

FINE_MULTIPLIER = Decimal("2")


def create_stripe_session(borrowing, request):
    days = (borrowing.expected_return_date - borrowing.borrow_date).days
    total_price = borrowing.book.daily_fee * days
    amount_in_cents = int(total_price * 100)

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
        success_url=request.build_absolute_uri("/api/payments/success/")
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri("api/payments/cancel"),
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
    days_overdue = (borrowing.actual_return_date - borrowing.expected_return_date).days
    fine_amount = borrowing.book.daily_fee * days_overdue * FINE_MULTIPLIER
    amount_in_cents = int(fine_amount * 100)

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
        success_url=request.build_absolute_uri("/api/payments/success/")
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri("/api/payments/cancel/"),
    )

    Payment.objects.create(
        borrowing=borrowing,
        status=Payment.Status.PENDING,
        type=Payment.Type.FINE,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=fine_amount,
    )
