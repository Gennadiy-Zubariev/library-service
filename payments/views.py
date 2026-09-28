import stripe
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

        return queryset.filter(user=self.request.user)


class PaymentSuccessView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.InvalidRequestError:
            return Response(
                {"error": "Invalid session_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if session.payment_status == "paid":
            payment.status = Payment.Status.PAID
            payment.save()
            return Response(
                {
                    "message": "Payment successful",
                    "payment": PaymentSerializer(payment).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "Payment not complated yet"}, status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            {
                "message": "Payment can be made later. Session is available for 24 hours."
            },
            status=status.HTTP_200_OK,
        )
