from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from books.models import Book
from borrowings.models import Borrowing
from notifications.tasks import check_overdue_borrowings
from notifications.telegram import send_telegram_message

User = get_user_model()


class TelegramNotificationTest(TestCase):

    @patch("notifications.telegram.requests.post")
    def test_send_message_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        send_telegram_message("Test")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        self.assertEqual(call_kwargs.kwargs["json"]["text"], "Test")

    @patch("notifications.telegram.requests.post")
    def test_send_message_includes_chat_id(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        send_telegram_message("Test")
        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("chat_id", payload)

    @patch("notifications.telegram.requests.post")
    def test_send_message_uses_html_parse_mode(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        send_telegram_message("Test")
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["parse_mode"], "HTML")

    @patch("notifications.telegram.requests.post")
    def test_send_message_api_error_no_crash(self, mock_post):
        mock_post.side_effect = requests.RequestException("Connection error")
        # Should not raise
        send_telegram_message("Test message")

    @override_settings(TELEGRAM_BOT_TOKEN=None)
    @patch("notifications.telegram.requests.post")
    def test_skip_when_token_missing(self, mock_post):
        send_telegram_message("Test message")
        mock_post.assert_not_called()


class OverdueNotificationTest(TestCase):
    @patch("notifications.tasks.send_telegram_message")
    @patch("notifications.tasks.date")
    def test_overdue_message_escapes_user_values(self, mock_date, mock_send):
        user = User.objects.create_user(email="john_doe@test.com", password="test12345")
        book = Book.objects.create(
            title="Tom & <Jerry>",
            author="Author",
            cover=Book.CoverType.HARD,
            inventory=1,
            daily_fee=Decimal("1.50"),
        )
        Borrowing.objects.create(
            user=user,
            book=book,
            expected_return_date=date.today() + timedelta(days=1),
        )
        mock_date.today.return_value = date.today() + timedelta(days=5)

        check_overdue_borrowings()

        mock_send.assert_called_once()
        text = mock_send.call_args.args[0]
        self.assertIn("<b>Overdue Borrowing</b>", text)
        self.assertIn("Book: Tom &amp; &lt;Jerry&gt;", text)
        self.assertIn("User: john_doe@test.com", text)
        self.assertIn("Days overdue: 4", text)
