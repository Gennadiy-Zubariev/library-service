import hashlib
import hmac
import json
import time
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.stripe_helper import create_fine_session, create_stripe_session

User = get_user_model()

SUCCESS_URL = reverse("payments:payment-success")
PAYMENT_LIST_URL = reverse("payments:payment-list")
WEBHOOK_URL = reverse("payments:payment-webhook")
WEBHOOK_SECRET = "whsec_test_secret"


def create_payment(user, session_id="cs_test_owner"):
    book = Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover=Book.CoverType.HARD,
        inventory=5,
        daily_fee=Decimal("1.50"),
    )
    borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        expected_return_date=date.today() + timedelta(days=7),
    )
    return Payment.objects.create(
        borrowing=borrowing,
        type=Payment.Type.PAYMENT,
        session_id=session_id,
        session_url="https://checkout.stripe.com/test",
        money_to_pay=Decimal("10.50"),
    )


def stripe_session(payment_status="paid", **fields):
    """A real stripe Session object, same type that Session.retrieve returns."""
    return stripe.checkout.Session.construct_from(
        {"id": "cs_test", "payment_status": payment_status, **fields}, "sk_test"
    )


def session_fields(payment, **overrides):
    """Stripe session fields that match the given payment."""
    fields = {
        "amount_total": int(payment.money_to_pay * 100),
        "currency": "usd",
        "metadata": {
            "borrowing_id": str(payment.borrowing_id),
            "type": payment.type,
        },
    }
    fields.update(overrides)
    return fields


MISMATCHES = {
    "amount": {"amount_total": 100},
    "currency": {"currency": "eur"},
    "borrowing": {"metadata": {"borrowing_id": "999999", "type": "PAYMENT"}},
    "type": {"metadata": {"borrowing_id": "1", "type": "FINE"}},
    "no_metadata": {"metadata": {}},
}


class PaymentSessionIdUniqueTest(TestCase):
    def test_duplicate_session_id_raises_integrity_error(self):
        user = User.objects.create_user(email="dup@test.com", password="test12345")
        payment = create_payment(user, session_id="cs_test_dup")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                borrowing=payment.borrowing,
                type=Payment.Type.FINE,
                session_id="cs_test_dup",
                session_url="https://checkout.stripe.com/test2",
                money_to_pay=Decimal("5.00"),
            )

        self.assertEqual(Payment.objects.filter(session_id="cs_test_dup").count(), 1)


class PaymentUniquePerBorrowingTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="uniq@test.com", password="test12345")
        self.payment = create_payment(user, session_id="cs_test_first")

    def _create(self, payment_type, session_id):
        return Payment.objects.create(
            borrowing=self.payment.borrowing,
            type=payment_type,
            session_id=session_id,
            session_url="https://checkout.stripe.com/test2",
            money_to_pay=Decimal("5.00"),
        )

    def test_duplicate_borrowing_and_type_raises_integrity_error(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._create(Payment.Type.PAYMENT, "cs_test_second")

        self.assertEqual(Payment.objects.count(), 1)

    def test_payment_and_fine_for_same_borrowing_allowed(self):
        self._create(Payment.Type.FINE, "cs_test_fine")

        self.assertEqual(
            Payment.objects.filter(borrowing=self.payment.borrowing).count(), 2
        )


class PaymentSuccessViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", password="test12345"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test12345"
        )
        self.payment = create_payment(self.owner)

    def test_unauthenticated_forbidden(self):
        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_id_required(self):
        self.client.force_authenticate(self.owner)
        result = self.client.get(SUCCESS_URL)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_other_users_payment_returns_404(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid")
        self.client.force_authenticate(self.other_user)

        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        mock_retrieve.assert_not_called()
        mock_notify.delay.assert_not_called()

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_owner_marks_payment_paid(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = stripe_session(**session_fields(self.payment))
        self.client.force_authenticate(self.owner)

        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_repeated_call_sends_notification_once(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = stripe_session(**session_fields(self.payment))
        self.client.force_authenticate(self.owner)

        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_session_mismatch_returns_400_and_keeps_pending(
        self, mock_retrieve, mock_notify
    ):
        self.client.force_authenticate(self.owner)
        for name, overrides in MISMATCHES.items():
            with self.subTest(mismatch=name):
                mock_retrieve.return_value = stripe_session(
                    **session_fields(self.payment, **overrides)
                )

                result = self.client.get(
                    SUCCESS_URL, {"session_id": self.payment.session_id}
                )

                self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
                self.payment.refresh_from_db()
                self.assertEqual(self.payment.status, Payment.Status.PENDING)
                mock_notify.delay.assert_not_called()

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_unpaid_session_keeps_payment_pending(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = SimpleNamespace(payment_status="unpaid")
        self.client.force_authenticate(self.owner)

        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        mock_notify.delay.assert_not_called()


class PaymentListTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", password="test12345"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test12345"
        )
        self.staff = User.objects.create_user(
            email="staff@test.com", password="test12345", is_staff=True
        )
        self.own_payment = create_payment(self.owner, session_id="cs_test_own")
        self.foreign_payment = create_payment(
            self.other_user, session_id="cs_test_foreign"
        )

    def test_user_sees_only_own_payments(self):
        self.client.force_authenticate(self.owner)
        result = self.client.get(PAYMENT_LIST_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in result.data["results"]]
        self.assertEqual(ids, [self.own_payment.id])

    def test_staff_sees_all_payments(self):
        self.client.force_authenticate(self.staff)
        result = self.client.get(PAYMENT_LIST_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["count"], 2)


def signed_webhook_post(client, event, secret=WEBHOOK_SECRET):
    payload = json.dumps(event)
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256
    ).hexdigest()
    return client.post(
        WEBHOOK_URL,
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
    )


def session_event(event_type, session_id, payment_status="paid", **fields):
    return {
        "id": "evt_test",
        "object": "event",
        "type": event_type,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_status": payment_status,
                **fields,
            }
        },
    }


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
class StripeWebhookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", password="test12345"
        )
        self.payment = create_payment(self.owner)

    def test_invalid_signature_returns_400(self):
        event = session_event("checkout.session.completed", self.payment.session_id)
        with patch("payments.stripe_helper.send_telegram_notification") as mock_notify:
            result = signed_webhook_post(self.client, event, secret="whsec_wrong")

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        mock_notify.delay.assert_not_called()

    def test_missing_signature_returns_400(self):
        result = self.client.post(
            WEBHOOK_URL, data="{}", content_type="application/json"
        )
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_not_allowed(self):
        result = self.client.get(WEBHOOK_URL)
        self.assertEqual(result.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("payments.stripe_helper.send_telegram_notification")
    def test_completed_event_marks_payment_paid(self, mock_notify):
        event = session_event(
            "checkout.session.completed",
            self.payment.session_id,
            **session_fields(self.payment),
        )

        result = signed_webhook_post(self.client, event)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    def test_redelivered_event_sends_notification_once(self, mock_notify):
        event = session_event(
            "checkout.session.completed",
            self.payment.session_id,
            **session_fields(self.payment),
        )

        signed_webhook_post(self.client, event)
        signed_webhook_post(self.client, event)

        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    def test_session_mismatch_keeps_pending_and_logs_error(self, mock_notify):
        for name, overrides in MISMATCHES.items():
            with self.subTest(mismatch=name):
                event = session_event(
                    "checkout.session.completed",
                    self.payment.session_id,
                    **session_fields(self.payment, **overrides),
                )

                with self.assertLogs("payments.views", level="ERROR"):
                    result = signed_webhook_post(self.client, event)

                self.assertEqual(result.status_code, status.HTTP_200_OK)
                self.payment.refresh_from_db()
                self.assertEqual(self.payment.status, Payment.Status.PENDING)
                mock_notify.delay.assert_not_called()

    @patch("payments.stripe_helper.send_telegram_notification")
    def test_unpaid_completed_event_keeps_pending(self, mock_notify):
        event = session_event(
            "checkout.session.completed", self.payment.session_id, "unpaid"
        )

        result = signed_webhook_post(self.client, event)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        mock_notify.delay.assert_not_called()

    def test_unknown_session_returns_200(self):
        event = session_event("checkout.session.completed", "cs_test_unknown")
        result = signed_webhook_post(self.client, event)
        self.assertEqual(result.status_code, status.HTTP_200_OK)


@patch("payments.stripe_helper.stripe.checkout.Session.create")
class CreateFineSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="fine@test.com", password="test12345"
        )
        self.book = Book.objects.create(
            title="Fine Book",
            author="Fine Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=Decimal("1.50"),
        )
        self.request = SimpleNamespace(
            get_host=lambda: "testserver", is_secure=lambda: False
        )

    def _borrowing(self, actual_offset=None):
        today = date.today()
        return Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=today + timedelta(days=1),
            actual_return_date=(
                None if actual_offset is None else today + timedelta(days=actual_offset)
            ),
        )

    def test_active_borrowing_raises_validation_error(self, mock_create):
        borrowing = self._borrowing()

        with self.assertRaises(serializers.ValidationError):
            create_fine_session(borrowing, self.request)

        mock_create.assert_not_called()
        self.assertFalse(Payment.objects.exists())

    def test_returned_on_time_raises_validation_error(self, mock_create):
        borrowing = self._borrowing(actual_offset=1)

        with self.assertRaises(serializers.ValidationError):
            create_fine_session(borrowing, self.request)

        mock_create.assert_not_called()
        self.assertFalse(Payment.objects.exists())

    def test_overdue_creates_fine_payment(self, mock_create):
        mock_create.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/fine", id="cs_test_fine"
        )
        borrowing = self._borrowing(actual_offset=3)  # 2 days overdue

        create_fine_session(borrowing, self.request)

        payment = Payment.objects.get()
        self.assertEqual(payment.type, Payment.Type.FINE)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.money_to_pay, Decimal("6.00"))  # 1.50 * 2 * 2
        self.assertEqual(payment.session_id, "cs_test_fine")


@patch("payments.stripe_helper.stripe.checkout.Session.create")
class DuplicateSessionGuardTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="guard@test.com", password="test12345"
        )
        self.book = Book.objects.create(
            title="Guard Book",
            author="Guard Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=Decimal("1.50"),
        )
        self.request = SimpleNamespace(
            get_host=lambda: "testserver", is_secure=lambda: False
        )
        today = date.today()
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=today + timedelta(days=1),
            actual_return_date=today + timedelta(days=3),
        )

    def test_second_borrowing_payment_raises_validation_error(self, mock_create):
        mock_create.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/1", id="cs_test_1"
        )
        create_stripe_session(self.borrowing, self.request)

        with self.assertRaises(serializers.ValidationError):
            create_stripe_session(self.borrowing, self.request)

        mock_create.assert_called_once()
        self.assertEqual(Payment.objects.filter(type=Payment.Type.PAYMENT).count(), 1)

    def test_second_fine_raises_validation_error(self, mock_create):
        mock_create.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/2", id="cs_test_2"
        )
        create_fine_session(self.borrowing, self.request)

        with self.assertRaises(serializers.ValidationError):
            create_fine_session(self.borrowing, self.request)

        mock_create.assert_called_once()
        self.assertEqual(Payment.objects.filter(type=Payment.Type.FINE).count(), 1)

    def test_payment_and_fine_can_coexist(self, mock_create):
        mock_create.side_effect = [
            SimpleNamespace(url="https://checkout.stripe.com/3", id="cs_test_3"),
            SimpleNamespace(url="https://checkout.stripe.com/4", id="cs_test_4"),
        ]

        create_stripe_session(self.borrowing, self.request)
        create_fine_session(self.borrowing, self.request)

        self.assertEqual(Payment.objects.filter(borrowing=self.borrowing).count(), 2)
