from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

User = get_user_model()

SUCCESS_URL = reverse("payments:payment-success")
PAYMENT_LIST_URL = reverse("payments:payment-list")


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

    @patch("payments.views.send_telegram_notification")
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

    @patch("payments.views.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_owner_marks_payment_paid(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid")
        self.client.force_authenticate(self.owner)

        result = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.delay.assert_called_once()

    @patch("payments.views.send_telegram_notification")
    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_repeated_call_sends_notification_once(self, mock_retrieve, mock_notify):
        mock_retrieve.return_value = SimpleNamespace(payment_status="paid")
        self.client.force_authenticate(self.owner)

        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        mock_notify.delay.assert_called_once()

    @patch("payments.views.send_telegram_notification")
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
