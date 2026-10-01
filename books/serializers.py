from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee", "image")
        extra_kwargs = {
            "image": {"required": False, "allow_null": True},
            "inventory": {"min_value": 0},
        }
        read_only_fields = ("id",)
