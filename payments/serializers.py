from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "money_to_pay",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status != Payment.Status.PENDING:
            data["session_url"] = None
        return data
