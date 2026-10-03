from calendar import monthrange
from datetime import date

from django.db import models, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import LeadAssignment, Student, TrialLead, User
from core.permissions import IsCourseAdminOrManager

from core.domains.students.serializers import StudentSerializer
from core.domains.students.services import normalize_phone

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

        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "trial_lead_manage_forbidden"
            )

        group = serializer.validated_data.get(
            "group_assigned"
        )
        if group and group.company != user.company:
            raise PermissionDenied(
                "trial_group_forbidden"
            )

        lead = serializer.save(company=user.company)

        if user.role == User.Role.MANAGER:
            LeadAssignment.objects.get_or_create(
                lead=lead,
                defaults={"manager": user},
            )

    def perform_update(self, serializer):
        user = self.request.user

        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "trial_lead_manage_forbidden"
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
        if request.user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "trial_lead_manage_forbidden"
            )
        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="convert-to-student",
    )
    def convert_to_student(self, request, pk=None):
        lead = self.get_object()
        user = request.user

        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                "trial_lead_manage_forbidden"
            )

        if lead.company != user.company:
            raise PermissionDenied(
                "trial_lead_company_forbidden"
            )

        if not (
            lead.converted_to_student
            or lead.status == TrialLead.Status.CONVERTED
        ):
            return Response(
                {"detail": "trial_not_converted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            normalized_phone = normalize_phone(
                lead.phone or ""
            )
            existing_student = None

            if normalized_phone:
                for student in Student.objects.filter(
                    company=user.company,
                    archived_at__isnull=True,
                ).iterator():
                    if (
                        normalize_phone(student.phone or "")
                        == normalized_phone
                    ):
                        existing_student = student
                        break

            group = lead.group_assigned

            if existing_student:
                if group:
                    existing_student.groups.add(group)
                    if group.course_id:
                        existing_student.primary_course_id = (
                            group.course_id
                        )
                        existing_student.save(
                            update_fields=[
                                "primary_course",
                            ]
                        )

                lead.converted_to_student = True
                lead.status = TrialLead.Status.CONVERTED
                lead.trial_attended = True
                lead.save(
                    update_fields=[
                        "converted_to_student",
                        "status",
                        "trial_attended",
                    ]
                )

                return Response(
                    {
                        "created": False,
                        "student": StudentSerializer(
                            existing_student,
                            context={"request": request},
                        ).data,
                    }
                )

            full_name_parts = [
                part
                for part in (lead.full_name or "").strip().split()
                if part
            ]
            first_name = (
                full_name_parts[0]
                if full_name_parts
                else "Student"
            )
            last_name = " ".join(
                full_name_parts[1:]
            )

            notes_parts = []
            if lead.comment:
                notes_parts.append(lead.comment)
            if lead.course_interest:
                notes_parts.append(
                    f"Интерес к курсу: {lead.course_interest}"
                )
            if lead.source:
                notes_parts.append(
                    f"Источник: {lead.source}"
                )

            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "phone": lead.phone or "",
                "notes": "\n".join(notes_parts),
                "group_ids": (
                    [group.id]
                    if group
                    else []
                ),
                "primary_course": (
                    group.course_id
                    if group and group.course_id
                    else None
                ),
            }

            serializer = StudentSerializer(
                data=payload,
                context={"request": request},
            )
            serializer.is_valid(
                raise_exception=True
            )

            student = serializer.save(
                company=user.company
            )

            lead.converted_to_student = True
            lead.status = TrialLead.Status.CONVERTED
            lead.trial_attended = True
            lead.save(
                update_fields=[
                    "converted_to_student",
                    "status",
                    "trial_attended",
                ]
            )

            return Response(
                {
                    "created": True,
                    "student": StudentSerializer(
                        student,
                        context={"request": request},
                    ).data,
                },
                status=status.HTTP_201_CREATED,
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
                        "analytics_months_count_invalid"
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
                            "invalid_month_format"
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
                            "invalid_month_format"
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
