from rest_framework import serializers

from core.models import PromoCode, PromoRedemption


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



class PromoRedemptionSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="promo_code.code", read_only=True)
    reward_type = serializers.CharField(
        source="promo_code.reward_type",
        read_only=True,
    )
    reward_value = serializers.IntegerField(
        source="promo_code.reward_value",
        read_only=True,
    )
    activated_by = serializers.SerializerMethodField()
    activated_by_role = serializers.CharField(
        source="user.role",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = PromoRedemption
        fields = (
            "id",
            "code",
            "reward_type",
            "reward_value",
            "activated_at",
            "activated_by",
            "activated_by_role",
        )

    def get_activated_by(self, obj):
        if not obj.user:
            return None
        return obj.user.get_full_name() or obj.user.username
