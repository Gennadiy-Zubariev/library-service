from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from notifications.telegram import send_telegram_message


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
    def test_send_message_api_error_no_crash(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        # Should not raise
        send_telegram_message("Test message")

    @override_settings(TELEGRAM_BOT_TOKEN=None)
    @patch("notifications.telegram.requests.post")
    def test_skip_when_token_missing(self, mock_post):
        send_telegram_message("Test message")
        mock_post.assert_not_called()
