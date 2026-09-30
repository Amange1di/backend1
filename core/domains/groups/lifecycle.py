import logging

from django.utils import timezone

from core.models import Contract, Group, GroupMonth, User, UserBalance

logger = logging.getLogger(__name__)


class GroupLifecycleMixin:
    @staticmethod
    def _create_group_months(
        group: Group,
        months_count: int,
    ):
        if months_count < 1:
            GroupMonth.objects.filter(
                group=group
            ).delete()
            return

        GroupMonth.objects.filter(
            group=group,
            month_number__gt=months_count,
        ).delete()

        for month_number in range(
            1,
            months_count + 1,
        ):
            GroupMonth.objects.get_or_create(
                group=group,
                month_number=month_number,
                defaults={
                    "status": (
                        GroupMonth.Status.PENDING
                    )
                },
            )

    @staticmethod
    def _credit_teacher_percent_on_create(
        group,
        *,
        teacher,
        course,
        teacher_percent,
    ):
        if (
            not teacher
            or not course
            or not teacher_percent
            or teacher_percent <= 0
        ):
            return

        try:
            teacher_user = User.objects.get(
                id=teacher.id
            )
            course_price = course.price or 0
            student_count = (
                group.students.count()
                or 0
            )
            total_amount = (
                course_price
                * student_count
            )
            percent_amount = (
                total_amount
                * teacher_percent
            ) / 100

            if percent_amount <= 0:
                return

            teacher_balance, _ = (
                UserBalance.objects.get_or_create(
                    user=teacher_user
                )
            )
            reason = (
                f"Начисление %{teacher_percent}% "
                f"от группы «{group.name}» "
                f"({student_count} студ. × "
                f"{course_price} eC)"
            )
            teacher_balance.add_coins(
                int(percent_amount),
                reason,
            )
        except Exception:
            logger.exception(
                (
                    "Failed to credit teacher percent "
                    "on group create"
                )
            )

    @staticmethod
    def _credit_teacher_percent(
        group: Group,
        teacher_changed: bool = False,
        old_percent: float = 0,
        old_course=None,
    ):
        teacher = group.teacher
        course = group.course
        teacher_percent = (
            group.teacher_percent
            or 0
        )

        if (
            not teacher
            or not course
            or not teacher_percent
            or teacher_percent <= 0
        ):
            return

        student_count = (
            group.students.count()
            or 0
        )
        if student_count == 0:
            return

        try:
            teacher_user = User.objects.get(
                id=teacher.id
            )
            course_price = course.price or 0
            total_amount = (
                course_price
                * student_count
            )
            percent_amount = int(
                (
                    total_amount
                    * teacher_percent
                )
                / 100
            )

            if percent_amount <= 0:
                return

            teacher_balance, _ = (
                UserBalance.objects.get_or_create(
                    user=teacher_user
                )
            )

            if (
                (
                    teacher_changed
                    or old_percent
                    != teacher_percent
                    or old_course != course
                )
                and old_percent
                and old_percent > 0
            ):
                old_total = (
                    (old_course.price or 0)
                    * student_count
                )
                old_amount = int(
                    (
                        old_total
                        * old_percent
                    )
                    / 100
                )

                if old_amount > 0:
                    teacher_balance.spend_coins(
                        old_amount,
                        (
                            "Корректировка: списание "
                            f"%{old_percent}% группы "
                            f"«{group.name}»"
                        ),
                    )

            reason = (
                f"Начисление %{teacher_percent}% "
                f"от группы «{group.name}» "
                f"({student_count} студ. × "
                f"{course_price} eC)"
            )
            teacher_balance.add_coins(
                percent_amount,
                reason,
            )
        except Exception:
            logger.exception(
                (
                    "Failed to credit teacher percent "
                    "for group %s"
                ),
                group.id,
            )

    @staticmethod
    def _create_contracts(
        group,
        *,
        user,
        course,
        students,
    ):
        if not course or not students:
            return

        for student in students:
            if Contract.objects.filter(
                student=student,
                group=group,
            ).exists():
                continue

            try:
                Contract.objects.create(
                    company=user.company,
                    student=student,
                    group=group,
                    amount=course.price or 0,
                    start_date=(
                        group.start_date
                        or timezone.now().date()
                    ),
                    end_date=group.end_date,
                    created_by=user,
                    status=Contract.Status.DRAFT,
                )
            except Exception:
                logger.exception(
                    (
                        "Failed to auto-create "
                        "contract for student %s"
                    ),
                    student.id,
                )

    @staticmethod
    def _notify_teacher(group):
        try:
            from asgiref.sync import async_to_sync
            from telegram_bot.notifications import (
                send_group_request_notification,
            )

            fresh_group = (
                Group.objects.select_related(
                    "teacher"
                ).get(id=group.id)
            )

            if (
                fresh_group.teacher
                and fresh_group.teacher.telegram_chat_id
            ):
                async_to_sync(
                    send_group_request_notification
                )(fresh_group)
        except Exception:
            logger.exception(
                (
                    "Failed to send group "
                    "notification to teacher"
                )
            )
