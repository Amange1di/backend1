from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Expense, Group, User
from core.permissions import IsCourseAdminOrManagerReadOnly
from finance.models import SalaryRecord
from finance.serializers import SalaryRecordSerializer


class SalaryRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCourseAdminOrManagerReadOnly]
    serializer_class = SalaryRecordSerializer

    def _company(self):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            return user.company
        return None

    def get_queryset(self):
        company = self._company()
        if not company:
            return SalaryRecord.objects.none()

        qs = SalaryRecord.objects.filter(company=company).select_related("employee")

        employee_role = self.request.query_params.get("role")
        status_value = self.request.query_params.get("status")
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")

        if employee_role:
            qs = qs.filter(employee__role=employee_role)
        if status_value:
            qs = qs.filter(status=status_value)
        if year and year.isdigit():
            qs = qs.filter(year=int(year))
        if month and month.isdigit():
            qs = qs.filter(month=int(month))

        return qs

    def perform_create(self, serializer):
        serializer.save(company=self._company())

    def _expense_description(self, record):
        return (
            f"Зарплата сотрудника #{record.id}: "
            f"{record.employee.get_full_name() or record.employee.username} — "
            f"{record.month:02d}.{record.year}"
        )

    def _sync_salary_expense(self, record):
        description = self._expense_description(record)

        if record.status != SalaryRecord.Status.PAID or not record.paid_at:
            Expense.objects.filter(
                company=record.company,
                description=description,
            ).delete()
            return

        Expense.objects.update_or_create(
            company=record.company,
            description=description,
            defaults={
                "amount": record.total_amount,
                "category": "salary",
                "date": record.paid_at,
            },
        )

    def perform_update(self, serializer):
        record = serializer.save()
        self._sync_salary_expense(record)

    def perform_destroy(self, instance):
        Expense.objects.filter(
            company=instance.company,
            description=self._expense_description(instance),
        ).delete()
        instance.delete()

    @action(detail=False, methods=["get"])
    def employees(self, request):
        company = self._company()
        if not company:
            return Response([])

        employees = (
            User.objects.filter(
                company=company,
                role__in=[User.Role.TEACHER, User.Role.MANAGER],
                is_active=True,
            )
            .order_by("role", "first_name", "last_name")
        )

        return Response([
            {
                "id": employee.id,
                "name": employee.get_full_name() or employee.username,
                "role": employee.role,
                "salary_rate": float(employee.salary_rate or 0),
            }
            for employee in employees
        ])

    def _teacher_percent_for_month(self, employee, year, month):
        month_end = date(year, month, monthrange(year, month)[1])
        total = Decimal("0")

        groups = Group.objects.filter(
            company=employee.company,
            teacher=employee,
            course__isnull=False,
        ).select_related("course")

        for group in groups:
            teacher_percent = group.teacher_percent or Decimal("0")
            if teacher_percent <= 0:
                continue

            student_count = group.students.filter(
                created_at__date__lte=month_end
            ).count()
            if student_count <= 0:
                continue

            total += (
                group.course.price
                * Decimal(student_count)
                * teacher_percent
                / Decimal("100")
            )

        return total.quantize(Decimal("0.01"))

    @action(detail=False, methods=["post"], url_path="generate-month")
    def generate_month(self, request):
        company = self._company()
        if not company:
            return Response(
                {"detail": "Компания не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year = int(request.data.get("year", timezone.localdate().year))
            month = int(request.data.get("month", timezone.localdate().month))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Некорректный год или месяц."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= month <= 12:
            return Response(
                {"detail": "Месяц должен быть от 1 до 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employees = User.objects.filter(
            company=company,
            role__in=[User.Role.TEACHER, User.Role.MANAGER],
            is_active=True,
            date_joined__date__lte=date(year, month, monthrange(year, month)[1]),
        )

        created = 0
        updated = 0

        with transaction.atomic():
            for employee in employees:
                percent_amount = Decimal("0")
                if employee.role == User.Role.TEACHER:
                    percent_amount = self._teacher_percent_for_month(
                        employee,
                        year,
                        month,
                    )

                record, was_created = SalaryRecord.objects.update_or_create(
                    company=company,
                    employee=employee,
                    year=year,
                    month=month,
                    defaults={
                        "base_salary": employee.salary_rate or Decimal("0"),
                        "percent_amount": percent_amount,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

                self._sync_salary_expense(record)

        return Response({
            "created": created,
            "updated": updated,
            "records": SalaryRecordSerializer(
                SalaryRecord.objects.filter(
                    company=company,
                    year=year,
                    month=month,
                ).select_related("employee"),
                many=True,
            ).data,
        })

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        record = self.get_object()

        paid_at_raw = request.data.get("paid_at")
        if paid_at_raw:
            try:
                paid_at = date.fromisoformat(str(paid_at_raw))
            except ValueError:
                return Response(
                    {"detail": "Некорректная дата выплаты."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            paid_at = timezone.localdate()

        record.status = SalaryRecord.Status.PAID
        record.paid_at = paid_at
        record.save(update_fields=["status", "paid_at", "updated_at"])
        self._sync_salary_expense(record)

        return Response(SalaryRecordSerializer(record).data)

    @action(detail=True, methods=["post"], url_path="mark-pending")
    def mark_pending(self, request, pk=None):
        record = self.get_object()
        record.status = SalaryRecord.Status.PENDING
        record.paid_at = None
        record.save(update_fields=["status", "paid_at", "updated_at"])
        self._sync_salary_expense(record)

        return Response(SalaryRecordSerializer(record).data)
