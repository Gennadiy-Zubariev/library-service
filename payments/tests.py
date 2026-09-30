import hashlib
import hmac
import json
import time
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

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
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid")
        self.client.force_authenticate(self.owner)

        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_repeated_call_sends_notification_once(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid")
        self.client.force_authenticate(self.owner)

        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        mock_notify.delay.assert_called_once()

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


def session_event(event_type, session_id, payment_status="paid"):
    return {
        "id": "evt_test",
        "object": "event",
        "type": event_type,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_status": payment_status,
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
        event = session_event("checkout.session.completed", self.payment.session_id)

        result = signed_webhook_post(self.client, event)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.delay.assert_called_once()

    @patch("payments.stripe_helper.send_telegram_notification")
    def test_redelivered_event_sends_notification_once(self, mock_notify):
        event = session_event("checkout.session.completed", self.payment.session_id)

        signed_webhook_post(self.client, event)
        signed_webhook_post(self.client, event)

        mock_notify.delay.assert_called_once()

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
