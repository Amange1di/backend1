from calendar import monthrange
from datetime import date

from django.db import models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import TrialLead, User
from core.permissions import IsCourseAdminOrManager

from .serializers import TrialLeadSerializer
from .services import compute_age_groups


class TrialLeadViewSet(viewsets.ModelViewSet):
    queryset = (
        TrialLead.objects.all()
        .select_related("assignment__manager")
        .order_by("-created_at")
    )
    serializer_class = TrialLeadSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            return queryset.filter(
                company=user.company
            )

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            return queryset.filter(
                company=user.company
            )

        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != User.Role.MANAGER:
            raise PermissionDenied(
                "Only managers can create trial leads."
            )

        group = serializer.validated_data.get(
            "group_assigned"
        )
        if group and group.company != user.company:
            raise PermissionDenied(
                "Not allowed for this group."
            )

        serializer.save(company=user.company)

    def perform_update(self, serializer):
        user = self.request.user

        if user.role != User.Role.MANAGER:
            raise PermissionDenied(
                "Only managers can update trial leads."
            )

        group = serializer.validated_data.get(
            "group_assigned"
        )
        if group and group.company != user.company:
            raise PermissionDenied(
                "Not allowed for this group."
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.MANAGER:
            raise PermissionDenied(
                "Only managers can delete trial leads."
            )
        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="analytics",
    )
    def analytics(self, request):
        months_param = request.query_params.get(
            "months",
            "",
        ).strip()
        months = [
            month.strip()
            for month in months_param.split(",")
            if month.strip()
        ]

        if not months:
            today = date.today()
            months = [
                f"{today.year:04d}-{today.month:02d}"
            ]

        if len(months) < 1 or len(months) > 6:
            return Response(
                {
                    "detail": (
                        "Months count must be between 1 and 6."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        parsed_months = []
        for value in months:
            parts = value.split("-")
            if len(parts) != 2:
                return Response(
                    {
                        "detail": (
                            "Invalid month format. Use YYYY-MM."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                year = int(parts[0])
                month = int(parts[1])
                if month < 1 or month > 12:
                    raise ValueError()
            except ValueError:
                return Response(
                    {
                        "detail": (
                            "Invalid month format. Use YYYY-MM."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            parsed_months.append(
                (value, year, month)
            )

        queryset = self.get_queryset()
        monthly_data = []
        sources_by_month = []
        ages_by_month = []

        total_leads = 0
        attended_total = 0
        not_attended_total = 0
        converted_total = 0

        for value, year, month in parsed_months:
            last_day = monthrange(
                year,
                month,
            )[1]
            start_date = date(
                year,
                month,
                1,
            )
            end_date = date(
                year,
                month,
                last_day,
            )

            month_qs = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )

            total = month_qs.count()
            attended = month_qs.filter(
                trial_attended=True
            ).count()
            not_attended = month_qs.filter(
                status=TrialLead.Status.NOT_ATTENDED
            ).count()
            converted = month_qs.filter(
                models.Q(converted_to_student=True)
                | models.Q(
                    status=TrialLead.Status.CONVERTED
                )
            ).count()

            conversion_rate = round(
                (converted / total * 100)
                if total
                else 0,
                2,
            )

            total_leads += total
            attended_total += attended
            not_attended_total += not_attended
            converted_total += converted

            monthly_data.append(
                {
                    "month": value,
                    "total_leads": total,
                    "attended_trial": attended,
                    "not_attended": not_attended,
                    "converted_students": converted,
                    "conversion_rate": (
                        conversion_rate
                    ),
                }
            )

            sources_raw = (
                month_qs.values("source")
                .annotate(
                    total=models.Count("id")
                )
                .order_by("-total")
            )
            sources_items = [
                {
                    "label": item["source"] or "—",
                    "total": item["total"],
                }
                for item in sources_raw
            ]
            sources_by_month.append(
                {
                    "month": value,
                    "items": sources_items,
                }
            )

            ages_by_month.append(
                {
                    "month": value,
                    "items": compute_age_groups(
                        month_qs
                    ),
                }
            )

        summary_rate = round(
            (
                converted_total
                / total_leads
                * 100
            )
            if total_leads
            else 0,
            2,
        )

        return Response(
            {
                "months": [
                    value
                    for value, _, _ in parsed_months
                ],
                "summary": {
                    "total_leads": total_leads,
                    "attended_trial": attended_total,
                    "not_attended": not_attended_total,
                    "converted_students": (
                        converted_total
                    ),
                    "conversion_rate": (
                        summary_rate
                    ),
                },
                "monthly_data": monthly_data,
                "sources": sources_by_month,
                "age_groups": ages_by_month,
            }
        )
