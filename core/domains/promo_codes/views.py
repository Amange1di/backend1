from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import (
    CompanyBalance,
    PromoBalance,
    PromoCode,
    PromoRedemption,
    User,
)
from core.audit import write_audit

from .serializers import PromoCodeSerializer, PromoRedemptionSerializer


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
        methods=["get"],
        url_path="history",
    )
    def history(self, request):
        user = request.user

        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "Only course admins and managers can view promo history."
            )

        company = getattr(user, "company", None)
        if not company:
            return Response([])

        redemptions = (
            PromoRedemption.objects
            .filter(company=company)
            .select_related("promo_code", "user")
            .order_by("-activated_at")
        )

        return Response(
            PromoRedemptionSerializer(
                redemptions,
                many=True,
            ).data
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
                "Only admins, course admins and managers can activate promo codes."
            )

        code = (request.data.get("code", "") or "").strip()
        if not code:
            return Response(
                {"detail": "Promo code is required."},
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
                {"detail": "Компания не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                promo_code = (
                    PromoCode.objects
                    .select_for_update()
                    .select_related("created_by")
                    .get(code=code)
                )
            except PromoCode.DoesNotExist:
                return Response(
                    {"detail": "Promo code not found."},
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
                                "Вы можете активировать только промокоды "
                                "созданные супер-админом."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            if not promo_code.is_active:
                return Response(
                    {"detail": "Promo code is inactive."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                promo_code.expiry_date
                and promo_code.expiry_date < timezone.now()
            ):
                return Response(
                    {"detail": "Cannot activate expired promo code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if promo_code.current_usages >= promo_code.max_usages:
                return Response(
                    {"detail": "Promo code usage limit reached."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if promo_code.reward_type != PromoCode.RewardType.COINS:
                return Response(
                    {
                        "detail": (
                            "This promo reward type is not enabled yet."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ledger_reason = f"Промокод: {promo_code.code}"

            try:
                promo_balance = (
                    PromoBalance.objects
                    .select_for_update()
                    .get(promo_code=promo_code)
                )
            except PromoBalance.DoesNotExist:
                return Response(
                    {"detail": "Promo code has no funded balance."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if promo_balance.balance < promo_code.reward_value:
                return Response(
                    {"detail": "Promo code balance is insufficient."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                with transaction.atomic():
                    PromoRedemption.objects.create(
                        promo_code=promo_code,
                        company=company,
                        user=user,
                    )
            except IntegrityError:
                return Response(
                    {"detail": "Promo code already used by this company."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not promo_balance.spend_coins(promo_code.reward_value):
                raise RuntimeError(
                    "Promo balance changed unexpectedly while locked."
                )

            company_balance, _ = CompanyBalance.objects.get_or_create(
                company=company,
                defaults={"balance": 0},
            )
            company_balance.add_coins(
                promo_code.reward_value,
                ledger_reason,
            )

            promo_code.current_usages += 1
            promo_code.save(update_fields=["current_usages"])

        write_audit(
            request,
            action="promo.redeemed",
            obj=promo_code,
            company=company,
            after={
                "reward_value": promo_code.reward_value,
                "current_usages": promo_code.current_usages,
            },
        )

        return Response(
            PromoCodeSerializer(promo_code).data
        )
