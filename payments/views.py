import stripe
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.tasks import send_telegram_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing")

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(borrowing__user=self.request.user)


class PaymentSuccessView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Stripe Checkout session ID",
                required=True,
            ),
        ],
        responses={
            200: inline_serializer(
                name="PaymentSuccessResponse",
                fields={
                    "message": serializers.CharField(),
                    "payment": PaymentSerializer(),
                },
            ),
            400: inline_serializer(
                name="PaymentErrorResponse",
                fields={"error": serializers.CharField()},
            ),
            404: inline_serializer(
                name="PaymentNotFoundResponse",
                fields={"error": serializers.CharField()},
            ),
        },
    )
    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            payment = Payment.objects.select_related(
                "borrowing__user", "borrowing__book"
            ).get(session_id=session_id, borrowing__user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.InvalidRequestError:
            return Response(
                {"error": "Invalid session_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        if session.payment_status == "paid":
            # Atomic PENDING -> PAID switch: only the request that actually
            # changes the status sends the notification (the endpoint can be
            # hit several times, e.g. React StrictMode or a page refresh).
            switched = Payment.objects.filter(
                pk=payment.pk, status=Payment.Status.PENDING
            ).update(status=Payment.Status.PAID)
            payment.status = Payment.Status.PAID
            if switched:
                send_telegram_notification.delay(
                    f"💰 *Payment Successful*\n"
                    f"Type: {payment.type}\n"
                    f"Amount: ${payment.money_to_pay}\n"
                    f"User: {payment.borrowing.user.email}\n"
                    f"Book: {payment.borrowing.book.title}"
                )
            return Response(
                {
                    "message": "Payment successful",
                    "payment": PaymentSerializer(payment).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "Payment not completed yet"}, status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: inline_serializer(
                name="PaymentCancelResponse",
                fields={"message": serializers.CharField()},
            ),
        },
    )
    def get(self, request):
        return Response(
            {
                "message": "Payment can be made later. Session is available for 24 hours."
            },
            status=status.HTTP_200_OK,
        )
