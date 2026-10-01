from html import escape

from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingReadSerializer,
    BorrowingReturnSerializer,
)
from notifications.tasks import send_telegram_notification
from payments.stripe_helper import create_fine_session, create_stripe_session


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=str,
                description="Filter by active borrowings (not returned yet). Use 'true'.",
                required=False,
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                description="Filter by user ID (admin only).",
                required=False,
            ),
        ]
    ),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book")

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id and user_id.isdigit():
                queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")
        if is_active and is_active.lower() == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "return_borrowing":
            return BorrowingReturnSerializer
        return BorrowingReadSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            borrowing = serializer.save(user=self.request.user)
            create_stripe_session(borrowing, self.request)
        send_telegram_notification.delay(
            f"📚 <b>New Borrowing</b>\n"
            f"Book: {escape(borrowing.book.title)}\n"
            f"User: {escape(borrowing.user.email)}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )

    @extend_schema(
        request=BorrowingReturnSerializer,
        responses=BorrowingReadSerializer,
    )
    @action(
        detail=True,
        methods=[
            "POST",
        ],
        url_path="return",
        url_name="return",
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        serializer = self.get_serializer(borrowing, data={})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
            if borrowing.actual_return_date > borrowing.expected_return_date:
                create_fine_session(borrowing, request)
        return Response(
            BorrowingReadSerializer(borrowing).data, status=status.HTTP_200_OK
        )
