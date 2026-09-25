from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from books.models import Book
from borrowings.serializers import BorrowingReadSerializer


class BorrowingView(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = BorrowingReadSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)
