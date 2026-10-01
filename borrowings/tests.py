from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

User = get_user_model()

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


def return_url(borrowing_id):
    return reverse("borrowings:borrowing-return", args=[borrowing_id])


def sample_book(**kwargs):
    defaults = {
        "title": "Test Book",
        "author": "Test Author",
        "cover": Book.CoverType.HARD,
        "inventory": 5,
        "daily_fee": Decimal("1.50"),
    }
    defaults.update(kwargs)
    return Book.objects.create(**defaults)


def sample_borrowing(user, book, **kwargs):
    defaults = {
        "expected_return_date": date.today() + timedelta(days=7),
    }
    defaults.update(kwargs)
    return Borrowing.objects.create(user=user, book=book, **defaults)


class UnauthorizedBorrowingTest(TestCase):
    def test_list_forbidden(self):
        client = APIClient()
        result = client.get(BORROWINGS_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class BorrowingListTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test12345"
        )
        self.book = sample_book()
        self.client.force_authenticate(user=self.user)

    def test_list_own_borrowings_only(self):
        sample_borrowing(self.user, self.book)
        sample_borrowing(self.other_user, self.book)
        result = self.client.get(BORROWINGS_URL)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data["results"]), 1)

    def test_filter_is_active(self):
        sample_borrowing(self.user, self.book, actual_return_date=date.today())
        active = sample_borrowing(self.user, self.book)

        result = self.client.get(BORROWINGS_URL, {"is_active": "true"})
        self.assertEqual(len(result.data["results"]), 1)
        self.assertEqual(result.data["results"][0]["id"], active.id)

    def test_detail_has_nested_book(self):
        borrowing = sample_borrowing(self.user, self.book)
        result = self.client.get(detail_url(borrowing.id))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["book"]["title"], self.book.title)

    def test_detail_other_user_not_found(self):
        borrowing = sample_borrowing(self.other_user, self.book)
        result = self.client.get(detail_url(borrowing.id))
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)


class AdminBorrowingListTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com", password="test12345", is_staff=True
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.book = sample_book()
        self.client.force_authenticate(user=self.admin)

    def test_admin_sees_all(self):
        sample_borrowing(self.admin, self.book)
        sample_borrowing(self.user, self.book)
        result = self.client.get(BORROWINGS_URL)
        self.assertEqual(len(result.data["results"]), 2)

    def test_admin_filter_by_user_id(self):
        sample_borrowing(self.admin, self.book)
        sample_borrowing(self.user, self.book)
        result = self.client.get(BORROWINGS_URL, {"user_id": self.user.id})
        self.assertEqual(len(result.data["results"]), 1)


class BorrowingCreateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.book = sample_book(inventory=2)
        self.client.force_authenticate(user=self.user)

    def test_create_success(self):
        data = {
            "book": self.book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }
        result = self.client.post(BORROWINGS_URL, data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

    def test_create_attaches_current_user(self):
        data = {
            "book": self.book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }
        self.client.post(BORROWINGS_URL, data)
        borrowing = Borrowing.objects.last()
        self.assertEqual(borrowing.user, self.user)

    def test_create_zero_inventory_forbidden(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }
        result = self.client.post(BORROWINGS_URL, data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def _post_with_date(self, expected_return_date):
        return self.client.post(
            BORROWINGS_URL,
            {"book": self.book.id, "expected_return_date": str(expected_return_date)},
        )

    def _assert_rejected(self, result):
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", result.data)
        self.assertFalse(Borrowing.objects.exists())
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_create_past_expected_return_date_returns_400(self):
        result = self._post_with_date(date.today() - timedelta(days=3))
        self._assert_rejected(result)

    def test_create_today_expected_return_date_returns_400(self):
        result = self._post_with_date(date.today())
        self._assert_rejected(result)

    def test_create_invalid_date_format_returns_400(self):
        result = self._post_with_date("2026-13-45")
        self._assert_rejected(result)

    @patch("borrowings.views.send_telegram_notification")
    @patch("borrowings.views.create_stripe_session")
    def test_create_tomorrow_expected_return_date_allowed(self, *_):
        result = self._post_with_date(date.today() + timedelta(days=1))
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

    @patch("borrowings.views.send_telegram_notification")
    @patch("borrowings.views.create_stripe_session")
    def test_create_notification_escapes_user_values(self, _, mock_notify):
        user = User.objects.create_user(email="john_doe@test.com", password="test12345")
        self.client.force_authenticate(user=user)
        book = sample_book(title="Tom & <Jerry>")

        result = self.client.post(
            BORROWINGS_URL,
            {
                "book": book.id,
                "expected_return_date": str(date.today() + timedelta(days=7)),
            },
        )

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        text = mock_notify.delay.call_args.args[0]
        self.assertIn("<b>New Borrowing</b>", text)
        self.assertIn("Book: Tom &amp; &lt;Jerry&gt;", text)
        self.assertIn("User: john_doe@test.com", text)


class BorrowingReturnTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.book = sample_book(inventory=3)
        self.borrowing = sample_borrowing(self.user, self.book)
        self.client.force_authenticate(user=self.user)

    def test_return_success(self):
        result = self.client.post(return_url(self.borrowing.id))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertEqual(self.borrowing.actual_return_date, date.today())
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 4)

    def test_return_twice_forbidden(self):
        self.client.post(return_url(self.borrowing.id))
        result = self.client.post(return_url(self.borrowing.id))
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_has_nested_book_in_response(self):
        result = self.client.post(return_url(self.borrowing.id))
        self.assertIn("book", result.data)
        self.assertEqual(result.data["book"]["title"], self.book.title)


@patch("payments.stripe_helper.stripe.checkout.Session.create")
class BorrowingReturnFineTest(TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.book = sample_book(inventory=3)
        self.borrowing = sample_borrowing(
            self.user, self.book, expected_return_date=date.today() + timedelta(days=1)
        )
        self.client.force_authenticate(user=self.user)

    def _return_three_days_later(self):
        late = datetime.now() + timedelta(days=3)  # 2 days overdue
        with patch("borrowings.serializers.timezone.now", return_value=late):
            return self.client.post(return_url(self.borrowing.id))

    def test_overdue_return_creates_fine_payment(self, mock_create):
        mock_create.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/fine", id="cs_test_fine"
        )

        result = self._return_three_days_later()

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        payment = Payment.objects.get(borrowing=self.borrowing)
        self.assertEqual(payment.type, Payment.Type.FINE)

    def test_stripe_failure_rolls_back_return(self, mock_create):
        mock_create.side_effect = stripe.StripeError("stripe is down")

        result = self._return_three_days_later()

        self.assertEqual(result.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.borrowing.refresh_from_db()
        self.assertIsNone(self.borrowing.actual_return_date)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)
        self.assertFalse(Payment.objects.exists())

    def test_return_can_be_retried_after_stripe_failure(self, mock_create):
        mock_create.side_effect = stripe.StripeError("stripe is down")
        self._return_three_days_later()
        mock_create.side_effect = None
        mock_create.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/fine", id="cs_test_fine"
        )

        result = self._return_three_days_later()

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.filter(type=Payment.Type.FINE).count(), 1)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 4)
