from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Expense, Group, User
from core.permissions import IsCourseAdminOrManagerReadOnly
from finance.models import SalaryPayment, SalaryRecord
from finance.serializers import SalaryPaymentSerializer, SalaryRecordSerializer


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

        qs = (
            SalaryRecord.objects.filter(company=company)
            .select_related("employee")
            .prefetch_related("payments", "payments__created_by")
        )

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
        employee = serializer.validated_data["employee"]
        year = serializer.validated_data["year"]
        month = serializer.validated_data["month"]

        percent_amount = Decimal("0")
        if employee.role == User.Role.TEACHER:
            percent_amount = self._teacher_percent_for_month(
                employee,
                year,
                month,
            )

        serializer.save(
            company=self._company(),
            percent_amount=percent_amount,
        )

    def perform_update(self, serializer):
        record = serializer.save()
        record.refresh_payment_status()

    def perform_destroy(self, instance):
        self._delete_record_expenses(instance)
        instance.delete()

    def _legacy_expense_description(self, record):
        return (
            f"Зарплата сотрудника #{record.id}: "
            f"{record.employee.get_full_name() or record.employee.username} — "
            f"{record.month:02d}.{record.year}"
        )

    def _payment_expense_description(self, payment):
        record = payment.salary_record
        return (
            f"Выплата зарплаты #{payment.id} / начисление #{record.id}: "
            f"{record.employee.get_full_name() or record.employee.username} — "
            f"{record.month:02d}.{record.year}"
        )

    def _sync_payment_expense(self, payment):
        Expense.objects.update_or_create(
            company=payment.salary_record.company,
            description=self._payment_expense_description(payment),
            defaults={
                "amount": payment.amount,
                "category": "salary",
                "date": payment.paid_at,
            },
        )

    def _delete_payment_expense(self, payment):
        Expense.objects.filter(
            company=payment.salary_record.company,
            description=self._payment_expense_description(payment),
        ).delete()

    def _delete_record_expenses(self, record):
        for payment in record.payments.all():
            self._delete_payment_expense(payment)

        Expense.objects.filter(
            company=record.company,
            description=self._legacy_expense_description(record),
        ).delete()

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
            date_joined__date__lte=date(
                year,
                month,
                monthrange(year, month)[1],
            ),
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

                record.refresh_payment_status()

                if was_created:
                    created += 1
                else:
                    updated += 1

        records = (
            SalaryRecord.objects.filter(
                company=company,
                year=year,
                month=month,
            )
            .select_related("employee")
            .prefetch_related("payments", "payments__created_by")
        )

        return Response({
            "created": created,
            "updated": updated,
            "records": SalaryRecordSerializer(
                records,
                many=True,
                context={"request": request},
            ).data,
        })

    @action(detail=True, methods=["post"], url_path="add-payment")
    def add_payment(self, request, pk=None):
        record = self.get_object()

        try:
            amount = Decimal(str(request.data.get("amount", "")))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {"detail": "Некорректная сумма выплаты."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"detail": "Сумма выплаты должна быть больше нуля."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        remaining = record.remaining_amount
        if amount > remaining:
            return Response(
                {
                    "detail": (
                        f"Сумма выплаты превышает остаток. "
                        f"Осталось выплатить: {remaining}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        payment_type = request.data.get(
            "payment_type",
            SalaryPayment.PaymentType.SALARY,
        )
        valid_types = {choice[0] for choice in SalaryPayment.PaymentType.choices}
        if payment_type not in valid_types:
            return Response(
                {"detail": "Некорректный тип выплаты."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SalaryPaymentSerializer(
            data={
                "amount": amount,
                "paid_at": paid_at,
                "payment_type": payment_type,
                "note": str(request.data.get("note", "")).strip(),
            }
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            payment = serializer.save(
                salary_record=record,
                created_by=request.user,
            )
            self._sync_payment_expense(payment)
            record.refresh_payment_status()

        record = self.get_queryset().get(pk=record.pk)
        return Response(
            SalaryRecordSerializer(
                record,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"payments/(?P<payment_id>[^/.]+)",
    )
    def delete_payment(self, request, pk=None, payment_id=None):
        record = self.get_object()

        try:
            payment = record.payments.get(pk=payment_id)
        except SalaryPayment.DoesNotExist:
            return Response(
                {"detail": "Выплата не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            self._delete_payment_expense(payment)
            payment.delete()
            record.refresh_payment_status()

        record = self.get_queryset().get(pk=record.pk)
        return Response(
            SalaryRecordSerializer(
                record,
                context={"request": request},
            ).data
        )

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        record = self.get_object()
        remaining = record.remaining_amount

        if remaining <= 0:
            record.refresh_payment_status()
            return Response(
                SalaryRecordSerializer(
                    record,
                    context={"request": request},
                ).data
            )

        mutable_data = request.data.copy()
        mutable_data["amount"] = str(remaining)
        mutable_data.setdefault(
            "payment_type",
            SalaryPayment.PaymentType.SALARY,
        )
        request._full_data = mutable_data
        return self.add_payment(request, pk=pk)

    @action(detail=True, methods=["post"], url_path="mark-pending")
    def mark_pending(self, request, pk=None):
        record = self.get_object()

        with transaction.atomic():
            self._delete_record_expenses(record)
            record.payments.all().delete()
            record.refresh_payment_status()

        record = self.get_queryset().get(pk=record.pk)
        return Response(
            SalaryRecordSerializer(
                record,
                context={"request": request},
            ).data
        )
