from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        max_length=7, choices=Status.choices, default=Status.PENDING
    )
    type = models.CharField(
        max_length=7,
        choices=Type.choices,
    )
    borrowing = models.ForeignKey(
        "borrowings.Borrowing", on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255, unique=True)
    money_to_pay = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.type} - {self.status} - {self.money_to_pay}"
