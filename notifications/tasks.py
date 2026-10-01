from datetime import date
from html import escape

from celery import shared_task

from borrowings.models import Borrowing
from notifications.telegram import send_telegram_message

TELEGRAM_LIMIT = 4096
HEADER = "⚠️ <b>Overdue Borrowings</b>"


def _chunk(blocks, limit):
    messages = []
    current = ""
    for block in blocks:
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > limit:
            messages.append(current)
            current = block
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages


@shared_task
def send_telegram_notification(text):
    send_telegram_message(text)


@shared_task
def check_overdue_borrowings():
    today = date.today()
    overdue = Borrowing.objects.select_related("book", "user").filter(
        expected_return_date__lte=today, actual_return_date__isnull=True
    )

    if not overdue:
        send_telegram_message("No borrowings overdue today!")
        return

    blocks = []
    for borrowing in overdue:
        blocks.append(
            f"Book: {escape(borrowing.book.title)}\n"
            f"User: {escape(borrowing.user.email)}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}\n"
            f"Days overdue: {(today - borrowing.expected_return_date).days}"
        )

    limit = TELEGRAM_LIMIT - len(HEADER) - 2
    for message in _chunk(blocks, limit):
        send_telegram_message(f"{HEADER}\n\n{message}")
