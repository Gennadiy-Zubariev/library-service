from django.db.models import Sum
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from borrowings.models import Borrowing


class StatsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "books_available": Book.objects.aggregate(total=Sum("inventory"))[
                    "total"
                ]
                or 0,
                "active_readers": Borrowing.objects.filter(
                    actual_return_date__isnull=True
                )
                .values("user")
                .distinct()
                .count(),
                "borrowings_total": Borrowing.objects.count(),
            }
        )
