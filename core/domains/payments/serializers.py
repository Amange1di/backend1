from rest_framework import serializers

from core.models import Company, Payment


class PaymentSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Payment
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
