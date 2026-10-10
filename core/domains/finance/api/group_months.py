import logging
from calendar import monthrange
from datetime import date

from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from core.models import (
    Expense,
    Group,
    GroupMonth,
    Payment,
    Student,
    User,
    UserBalance,
    UserTransaction,
)
from core.permissions import (
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
)

from ..serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)

logger = logging.getLogger(__name__)

class GroupMonthViewSet(viewsets.ModelViewSet):
    queryset = GroupMonth.objects.none()
    """
    CRUD для месяцев обучения группы.
    """
    permission_classes = [IsCourseAdminOrManagerReadOnly]
    serializer_class = GroupMonthSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN, User.Role.MANAGER):
            if user.company:
                qs = GroupMonth.objects.filter(group__company=user.company)
                if user.role != User.Role.COMPANY_OWNER:
                    qs = qs.filter(group__branch__in=user.branches.filter(is_active=True))
            else:
                return GroupMonth.objects.none()
        elif user.role == User.Role.TEACHER:
            qs = GroupMonth.objects.filter(group__teacher=user)
        else:
            return GroupMonth.objects.none()
        selected = self.request.COOKIES.get("eduosh_branch")
        if selected and selected.isdigit():
            branch_id = int(selected)
            if user.role != User.Role.COMPANY_OWNER and not user.branches.filter(id=branch_id, is_active=True).exists():
                raise PermissionDenied("branch_access_denied")
            qs = qs.filter(group__branch_id=branch_id)
        # Фильтр по группе, если передан параметр ?group=ID
        group_id = self.request.query_params.get("group")
        if group_id and group_id.isdigit():
            qs = qs.filter(group_id=int(group_id))
        # Фильтр по учителю, если передан параметр ?teacher_id=ID
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id and teacher_id.isdigit():
            qs = qs.filter(group__teacher_id=int(teacher_id))
        # Фильтр по месяцу, если передан параметр ?month_number=N
        month_number = self.request.query_params.get("month_number")
        if month_number and month_number.isdigit():
            qs = qs.filter(month_number=int(month_number))
        # Фильтр по статусу, если передан параметр ?status=pending|completed
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.select_related("group", "group__course").prefetch_related("group__students")

    def list(self, request, *args, **kwargs):
        # Auto-create все месяцы для группы, если их нет
        group_id = request.query_params.get("group")
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                if group.total_months and group.total_months > 0:
                    existing = set(GroupMonth.objects.filter(
                        group=group
                    ).values_list("month_number", flat=True))
                    for month_number in range(1, group.total_months + 1):
                        if month_number not in existing:
                            GroupMonth.objects.create(
                                group=group,
                                month_number=month_number,
                                status=GroupMonth.Status.PENDING,
                            )
            except Group.DoesNotExist:
                pass
        return super().list(request, *args, **kwargs)

    def _sync_expense_for_month(self, instance: GroupMonth):
        """
        При завершении месяца с зарплатой — создаёт/обновляет расход (Expense).
        При возврате в ожидание — удаляет расход.
        """
        group = instance.group
        if not group.company:
            return
        desc = f"Зарплата: {group.name} — месяц {instance.month_number}"
        if instance.status == GroupMonth.Status.COMPLETED and instance.teacher_salary:
            Expense.objects.update_or_create(
                company=group.company,
                description=desc,
                defaults={
                    "amount": instance.teacher_salary,
                    "category": "salary",
                    "branch": group.branch,
                    "date": instance.completed_at.date() if instance.completed_at else timezone.localdate(),
                },
            )
        elif instance.status == GroupMonth.Status.PENDING:
            Expense.objects.filter(
                company=group.company,
                description=desc,
            ).delete()

    def perform_update(self, serializer):
        """
        При закрытии месяца (completed_at установлен) —
        авто-создаём следующий месяц, если не превышен лимит total_months.
        """
        instance = serializer.save()

        # Проверяем, был ли месяц только что закрыт
        if instance.status == GroupMonth.Status.COMPLETED and instance.completed_at:
            group = instance.group
            next_month_number = instance.month_number + 1

            # Не создаём, если превышает total_months группы
            if not group.total_months or next_month_number > group.total_months:
                return

            # Создаём следующий месяц, если его ещё нет
            GroupMonth.objects.get_or_create(
                group=group,
                month_number=next_month_number,
                defaults={"status": GroupMonth.Status.PENDING},
            )

            # Автоматическое начисление % учителю при завершении месяца
            self._credit_teacher_percent_on_month_completion(instance)

    def _credit_teacher_percent_on_month_completion(self, instance: GroupMonth):
        """
        При завершении месяца начисляет учителю % от стоимости группы.
        Формула: students_count × course_price × teacher_percent / 100.
        Начисляется один раз за каждый завершённый месяц.
        """
        group = instance.group
        teacher = group.teacher
        teacher_percent = group.teacher_percent or 0
        course = group.course

        if not teacher or not course or not teacher_percent or teacher_percent <= 0:
            return

        student_count = group.students.count() or 0
        if student_count == 0:
            return

        try:
            teacher_user = User.objects.get(id=teacher.id)
            course_price = course.price or 0
            total_amount = course_price * student_count
            percent_amount = int((total_amount * teacher_percent) / 100)

            if percent_amount <= 0:
                return

            # Проверяем, не начислялось ли уже за этот месяц
            # Используем Q-объекты для OR-логики поиска по нескольким условиям
            from django.db.models import Q
            already_credited = UserTransaction.objects.filter(
                user=teacher_user,
                amount__gt=0,
                reason__contains=f"месяц {instance.month_number}",
            ).filter(
                Q(reason__contains=group.name) | Q(reason__contains=str(instance.month_number))
            ).exists()

            if already_credited:
                logger.info(
                    f"Teacher {teacher_user.username} already credited for month {instance.month_number} of group {group.name}"
                )
                return

            teacher_balance, created = UserBalance.objects.get_or_create(user=teacher_user)
            reason = (
                f"Начисление %{teacher_percent}% за месяц {instance.month_number} группы «{group.name}» "
                f"({student_count} студ. × {course_price} eC)"
            )
            teacher_balance.add_coins(percent_amount, reason)
            logger.info(
                f"Teacher {teacher_user.username} credited {percent_amount} eC "
                f"for month {instance.month_number} of group {group.name} "
                f"({teacher_percent}% of {student_count} students × {course_price} eC)"
            )
        except Exception as e:
            logger.warning(f"Failed to credit teacher percent on month completion for group {group.id}: {e}")
