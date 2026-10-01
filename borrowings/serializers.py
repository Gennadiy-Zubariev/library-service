from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user",
            "book",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")
        read_only_fields = ("id",)

    def validate_book(self, book):
        if book.inventory <= 0:
            raise serializers.ValidationError(
                "This book is not available (inventory = 0)"
            )
        return book

    def validate_expected_return_date(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError(
                "Expected return date must be later than today."
            )
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        pending_payments = Payment.objects.filter(
            borrowing__user=user, status=Payment.Status.PENDING
        ).exists()
        if pending_payments:
            raise serializers.ValidationError(
                "You cannot borrow books with pending payments. "
                "Please complete your outstanding payments first."
            )

        if Borrowing.objects.filter(
            user=user, book=attrs["book"], actual_return_date__isnull=True
        ).exists():
            raise serializers.ValidationError(
                "You already have an active borrowing of this book."
            )
        return attrs

    def create(self, validated_data):
        book = validated_data["book"]
        updated = Book.objects.filter(pk=book.pk, inventory__gt=0).update(
            inventory=F("inventory") - 1
        )
        if not updated:
            raise serializers.ValidationError(
                "This book is not available (inventory = 0)"
            )
        return super().create(validated_data)


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date")
        read_only_fields = ("id", "actual_return_date")

    def validate(self, attrs):
        if self.instance.actual_return_date is not None:
            raise serializers.ValidationError(
                "This borrowing has already been returned."
            )
        return attrs

    def save(self, **kwargs):
        today = timezone.now().date()
        with transaction.atomic():
            updated = Borrowing.objects.filter(
                pk=self.instance.pk, actual_return_date__isnull=True
            ).update(actual_return_date=today)
            if not updated:
                raise serializers.ValidationError(
                    "This borrowing has already been returned."
                )
            Book.objects.filter(pk=self.instance.book_id).update(
                inventory=F("inventory") + 1
            )
        self.instance.actual_return_date = today
        self.instance.book.refresh_from_db()
        return self.instance
