import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
)


def send_telegram_message(text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        responce = requests.post(TELEGRAM_API_URL, json=payload, timeout=5)
        responce.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send telegram notification: {e}")
