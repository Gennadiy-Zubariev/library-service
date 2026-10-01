from datetime import date
from html import escape

from celery import shared_task

from borrowings.models import Borrowing
from notifications.telegram import send_telegram_message


@shared_task
def send_telegram_notification(text):
    send_telegram_message(text)


@shared_task
def check_overdue_borrowings():
    overdue = Borrowing.objects.filter(
        expected_return_date__lte=date.today(), actual_return_date__isnull=True
    )

    if not overdue:
        send_telegram_message("No borrowings overdue today!")
        return

    for borrowing in overdue:
        send_telegram_message(
            f"⚠️ <b>Overdue Borrowing</b>\n"
            f"Book: {escape(borrowing.book.title)}\n"
            f"User: {escape(borrowing.user.email)}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}\n"
            f"Days overdue: {(date.today() - borrowing.expected_return_date).days}"
        )
