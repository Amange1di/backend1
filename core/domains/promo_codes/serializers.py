from rest_framework import serializers

from core.models import PromoCode


class PromoCodeSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = (
            "id",
            "code",
            "reward_type",
            "reward_value",
            "max_usages",
            "current_usages",
            "expiry_date",
            "is_active",
            "balance",
            "created_by",
            "created_at",
        )
        read_only_fields = (
            "current_usages",
            "created_by",
            "created_at",
            "balance",
        )

    def get_balance(self, obj):
        try:
            if (
                hasattr(obj, "balance")
                and obj.balance
            ):
                return obj.balance.balance
            return 0
        except Exception:
            return 0
