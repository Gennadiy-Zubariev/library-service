from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HARD", "Hard"
        SOFT = "SOFT", "Soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=CoverType.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to="books/", blank=True, null=True)

    def __str__(self):
        return f"{self.title} written by {self.author}"
