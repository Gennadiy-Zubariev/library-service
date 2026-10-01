from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

User = get_user_model()

BOOKS_URL = reverse("books:book-list")


def detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


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


class BookModeTests(TestCase):
    def test_str(self):
        book = sample_book()
        self.assertEqual(str(book), "Test Book written by Test Author")

    def test_negative_daily_fee_fails_validation(self):
        book = Book(
            title="T",
            author="A",
            cover=Book.CoverType.HARD,
            inventory=1,
            daily_fee=Decimal("-1.00"),
        )
        with self.assertRaises(ValidationError) as ctx:
            book.full_clean()
        self.assertIn("daily_fee", ctx.exception.message_dict)

    def test_negative_daily_fee_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            sample_book(daily_fee=Decimal("-1.00"))
        self.assertFalse(Book.objects.exists())

    def test_zero_daily_fee_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            sample_book(daily_fee=Decimal("0.00"))
        self.assertFalse(Book.objects.exists())

    def test_negative_inventory_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            sample_book(inventory=-1)
        self.assertFalse(Book.objects.exists())

    def test_cover_choice(self):
        book_hard = sample_book(title="Hard Book", cover=Book.CoverType.HARD)
        book_soft = sample_book(title="Soft Book", cover=Book.CoverType.SOFT)
        self.assertEqual(book_hard.cover, "HARD")
        self.assertEqual(book_soft.cover, "SOFT")


class BookViewTestUnauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_book_list(self):
        sample_book()
        sample_book(title="Test_2")
        result = self.client.get(BOOKS_URL)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["count"], 2)

    def test_book_detail(self):
        book = sample_book()
        result = self.client.get(detail_url(book.id))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["title"], book.title)

    def test_get_invalid_book(self):
        result = self.client.get(detail_url(999))
        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)


class BookViewTestAuthenticatedNotAdmin(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_book(self):
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": Book.CoverType.HARD,
            "inventory": 5,
            "daily_fee": "1.50",
        }
        result = self.client.post(BOOKS_URL, data)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_book(self):
        book = sample_book(title="For delete")
        result = self.client.delete(detail_url(book.id))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


class BookViewTestAdmin(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com", password="test12345", is_staff=True
        )
        self.book = sample_book()

        self.client.force_authenticate(user=self.admin)

    def test_create_book(self):
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": Book.CoverType.HARD,
            "inventory": 5,
            "daily_fee": "1.50",
        }
        result = self.client.post(BOOKS_URL, data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(id=result.data["id"])
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.daily_fee, Decimal("1.50"))

    def test_create_book_missing_fields(self):
        result = self.client.post(BOOKS_URL, {"title": "Only title"})
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_partial_update(self):
        result = self.client.patch(detail_url(self.book.id), {"inventory": 10})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(result.data["inventory"], self.book.inventory)

    def test_book_update(self):
        result = self.client.put(
            detail_url(self.book.id),
            {
                "title": "Test Book Update",
                "author": "Test Author Update",
                "cover": Book.CoverType.SOFT,
                "inventory": 7,
                "daily_fee": "20.50",
            },
        )
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(result.data["title"], self.book.title)
        self.assertEqual(result.data["author"], self.book.author)
        self.assertEqual(result.data["cover"], self.book.cover)
        self.assertEqual(result.data["inventory"], self.book.inventory)
        self.assertEqual(Decimal(result.data["daily_fee"]), self.book.daily_fee)

    def test_delete_book(self):
        book = sample_book(title="For delete")
        result = self.client.delete(detail_url(book.id))
        self.assertEqual(result.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(title="For delete").exists())

    def _book_data(self, daily_fee):
        return {
            "title": "Fee Book",
            "author": "Fee Author",
            "cover": Book.CoverType.HARD,
            "inventory": 5,
            "daily_fee": daily_fee,
        }

    def test_create_book_invalid_daily_fee_returns_400(self):
        for fee in ("-5.00", "0.00"):
            with self.subTest(daily_fee=fee):
                result = self.client.post(BOOKS_URL, self._book_data(fee))

                self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("daily_fee", result.data)
                self.assertFalse(Book.objects.filter(title="Fee Book").exists())

    def test_create_book_minimum_daily_fee_allowed(self):
        result = self.client.post(BOOKS_URL, self._book_data("0.01"))

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(id=result.data["id"])
        self.assertEqual(book.daily_fee, Decimal("0.01"))

    def test_update_book_negative_daily_fee_returns_400(self):
        result = self.client.patch(detail_url(self.book.id), {"daily_fee": "-1.00"})

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("daily_fee", result.data)
        self.book.refresh_from_db()
        self.assertEqual(self.book.daily_fee, Decimal("1.50"))

    def test_create_book_negative_inventory_returns_400(self):
        data = self._book_data("1.50")
        data["inventory"] = -1

        result = self.client.post(BOOKS_URL, data)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inventory", result.data)
        self.assertFalse(Book.objects.filter(title="Fee Book").exists())

    def test_create_book_zero_inventory_allowed(self):
        data = self._book_data("1.50")
        data["inventory"] = 0

        result = self.client.post(BOOKS_URL, data)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.get(id=result.data["id"]).inventory, 0)

    def test_partial_update_negative_inventory_returns_400(self):
        result = self.client.patch(detail_url(self.book.id), {"inventory": -5})

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inventory", result.data)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)

    def test_update_book_negative_inventory_returns_400(self):
        data = self._book_data("1.50")
        data["inventory"] = -5

        result = self.client.put(detail_url(self.book.id), data)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inventory", result.data)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)
