from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from books.models import Book
from borrowings.models import Borrowing
from notifications.tasks import _chunk, check_overdue_borrowings
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
        self.assertIn("<b>Overdue Borrowings</b>", text)
        self.assertIn("Book: Tom &amp; &lt;Jerry&gt;", text)
        self.assertIn("User: john_doe@test.com", text)
        self.assertIn("Days overdue: 4", text)


class ChunkTest(TestCase):
    def test_empty_blocks_give_no_messages(self):
        self.assertEqual(_chunk([], limit=100), [])

    def test_blocks_that_fit_go_into_one_message(self):
        self.assertEqual(_chunk(["a", "b", "c"], limit=100), ["a\n\nb\n\nc"])

    def test_blocks_are_split_when_limit_exceeded(self):
        blocks = ["A" * 40, "B" * 40, "C" * 40]

        messages = _chunk(blocks, limit=100)

        self.assertEqual(messages, ["A" * 40 + "\n\n" + "B" * 40, "C" * 40])

    def test_no_message_exceeds_limit_and_no_block_is_lost(self):
        blocks = [f"{i:02d}" + "x" * 30 for i in range(20)]

        messages = _chunk(blocks, limit=100)

        self.assertTrue(all(len(m) <= 100 for m in messages))
        self.assertEqual("\n\n".join(messages), "\n\n".join(blocks))


class OverdueDigestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="digest@test.com", password="test12345"
        )
        patcher = patch("notifications.tasks.date")
        mock_date = patcher.start()
        self.addCleanup(patcher.stop)
        mock_date.today.return_value = date.today() + timedelta(days=5)

    def _overdue_borrowing(self, title):
        book = Book.objects.create(
            title=title,
            author="Author",
            cover=Book.CoverType.HARD,
            inventory=1,
            daily_fee=Decimal("1.50"),
        )
        return Borrowing.objects.create(
            user=self.user,
            book=book,
            expected_return_date=date.today() + timedelta(days=1),
        )

    @patch("notifications.tasks.send_telegram_message")
    def test_no_overdue_sends_single_info_message(self, mock_send):
        check_overdue_borrowings()

        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.tasks.send_telegram_message")
    def test_many_overdue_borrowings_sent_in_one_message(self, mock_send):
        titles = [f"Book {i}" for i in range(5)]
        for title in titles:
            self._overdue_borrowing(title)

        check_overdue_borrowings()

        mock_send.assert_called_once()
        text = mock_send.call_args.args[0]
        for title in titles:
            self.assertIn(f"Book: {title}", text)

    @patch("notifications.tasks.send_telegram_message")
    def test_long_digest_is_split_within_telegram_limit(self, mock_send):
        titles = [f"{i:02d}" + "x" * 250 for i in range(20)]
        for title in titles:
            self._overdue_borrowing(title)

        check_overdue_borrowings()

        self.assertGreater(mock_send.call_count, 1)
        texts = [call.args[0] for call in mock_send.call_args_list]
        self.assertTrue(all(len(text) <= 4096 for text in texts))
        for title in titles:
            self.assertEqual(sum(title in text for text in texts), 1)

    @patch("notifications.tasks.send_telegram_message")
    def test_number_of_queries_does_not_grow_with_borrowings(self, mock_send):
        for i in range(3):
            self._overdue_borrowing(f"Book {i}")

        with self.assertNumQueries(1):
            check_overdue_borrowings()
