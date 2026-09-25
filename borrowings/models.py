from django.conf import settings
from django.db import models


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField()
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="borrowings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expected_return_date__gt=models.F("borrow_date")),
                name="expected_return_after_borrow",
            ),
            models.CheckConstraint(
                condition=models.Q(actual_return_date__gte=models.F("borrow_date")),
                name="actual_return_not_before_borrow",
            ),
        ]
        ordering = ["-borrow_date"]

    def __str__(self):
        return f"{self.book.title} - {self.user.email}"
