from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import (
    CompanyBalance,
    PromoCode,
    Transaction,
    User,
)
from .serializers import PromoCodeSerializer


class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all().order_by(
        "-created_at"
    )
    serializer_class = PromoCodeSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        user = self.request.user

        if (
            user.is_superuser
            or user.role
            in (
                User.Role.ADMIN,
                User.Role.SUPER_ADMIN,
            )
        ):
            return PromoCode.objects.all().order_by(
                "-created_at"
            )

        if user.role == User.Role.COURSE_ADMIN:
            return PromoCode.objects.filter(
                created_by=user
            ).order_by("-created_at")

        if user.role == User.Role.MANAGER:
            return PromoCode.objects.filter(
                created_by__role=User.Role.ADMIN
            ).order_by("-created_at")

        return PromoCode.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if not (
            user.is_superuser
            or user.role
            in (
                User.Role.ADMIN,
                User.Role.SUPER_ADMIN,
            )
        ):
            raise PermissionDenied(
                (
                    "Только админ может "
                    "создавать промокоды."
                )
            )

        serializer.save(
            created_by=self.request.user
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="activate",
    )
    def activate(self, request):
        user = request.user

        if user.role not in (
            User.Role.ADMIN,
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                (
                    "Only admins, course admins "
                    "and managers can activate "
                    "promo codes."
                )
            )

        code = (
            request.data.get(
                "code",
                "",
            ).strip()
        )
        if not code:
            return Response(
                {
                    "detail": (
                        "Promo code is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            promo_code = PromoCode.objects.get(
                code=code
            )
        except PromoCode.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Promo code not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            creator = promo_code.created_by
            creator_is_admin = (
                creator
                and (
                    creator.is_superuser
                    or creator.role
                    in (
                        User.Role.ADMIN,
                        User.Role.SUPER_ADMIN,
                    )
                )
            )
            if not creator_is_admin:
                return Response(
                    {
                        "detail": (
                            "Вы можете активировать "
                            "только промокоды созданные "
                            "супер-админом."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if (
            promo_code.expiry_date
            and promo_code.expiry_date
            < timezone.now()
        ):
            return Response(
                {
                    "detail": (
                        "Cannot activate expired "
                        "promo code."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            promo_code.current_usages
            >= promo_code.max_usages
        ):
            return Response(
                {
                    "detail": (
                        "Promo code usage limit reached."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not promo_code.is_active:
            return Response(
                {
                    "detail": (
                        "Promo code is inactive."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = (
            getattr(user, "company", None)
            or getattr(
                getattr(user, "created_by", None),
                "company",
                None,
            )
        )
        if not company:
            return Response(
                {
                    "detail": (
                        "Компания не найдена."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        company_balance, _ = (
            CompanyBalance.objects.get_or_create(
                company=company,
                defaults={"balance": 0},
            )
        )

        if (
            promo_code.reward_type
            == PromoCode.RewardType.COINS
        ):
            company_balance.add_coins(
                promo_code.reward_value,
                f"Промокод: {promo_code.code}",
            )
        else:
            Transaction.objects.create(
                company=company,
                user=user,
                amount=0,
                reason=(
                    "Промокод (бонус лимит): "
                    f"{promo_code.code}"
                ),
                transaction_type=(
                    Transaction.Type.BONUS
                ),
            )

        promo_code.current_usages += 1
        promo_code.save(
            update_fields=["current_usages"]
        )

        return Response(
            PromoCodeSerializer(
                promo_code
            ).data
        )
