from rest_framework import serializers

from core.models import Company, Payment


class PaymentSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Payment
        read_only_fields = ("company", "company_id", "reminder_sent_at", "created_at")

        fields = (
            "id",
            "student",
            "group",
            "company",
            "company_id",
            "amount",
            "status",
            "paid_at",
            "due_date",
            "reminder_sent_at",
            "created_at",
        )
