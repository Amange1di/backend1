from rest_framework import serializers

from core.models import Company, Payment


class PaymentSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(
        read_only=True,
    )
    received_by_name = serializers.SerializerMethodField()
    received_by_role = serializers.CharField(
        source="received_by.role",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Payment
        read_only_fields = (
            "company",
            "company_id",
            "received_by",
            "received_by_name",
            "received_by_role",
            "reminder_sent_at",
            "created_at",
        )

        fields = (
            "id",
            "student",
            "group",
            "branch",
            "company",
            "company_id",
            "received_by",
            "received_by_name",
            "received_by_role",
            "amount",
            "status",
            "paid_at",
            "due_date",
            "reminder_sent_at",
            "created_at",
        )


    def get_received_by_name(self, obj):
        if not obj.received_by:
            return None
        return (
            obj.received_by.get_full_name()
            or obj.received_by.username
        )
