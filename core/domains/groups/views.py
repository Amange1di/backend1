import logging

from django.db import models
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import (
    Contract,
    Group,
    GroupMonth,
    User,
    UserBalance,
)
from core.permissions import IsCourseAdminOrTeacherReadOnly

from .serializers import GroupSerializer
from .services import (
    compute_group_end_date,
    ensure_resource_available,
)

logger = logging.getLogger(__name__)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by(
        "-created_at"
    )
    serializer_class = GroupSerializer
    permission_classes = [
        IsCourseAdminOrTeacherReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            return queryset.filter(
                models.Q(course__admins=user)
                | models.Q(company=user.company)
            ).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            return queryset.filter(
                models.Q(
                    course__admins__company=user.company
                )
                | models.Q(company=user.company)
            ).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.TEACHER
        ):
            return queryset.filter(
                teacher=user
            )

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            return queryset.filter(
                students__user=user
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data.get(
            "course"
        )

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if not course:
                raise PermissionDenied(
                    "Not allowed for this course."
                )

            allowed = course.admins.filter(
                id=user.id
            ).exists()

            if user.role == User.Role.MANAGER:
                allowed = course.admins.filter(
                    company=user.company
                ).exists()

            if not allowed:
                raise PermissionDenied(
                    "Not allowed for this course."
                )

            teacher = serializer.validated_data.get(
                "teacher"
            )
            if (
                teacher
                and teacher.company != user.company
            ):
                raise PermissionDenied(
                    (
                        "Teacher must belong to "
                        "the same company."
                    )
                )

            if (
                teacher
                and not teacher.teaching_courses.filter(
                    id=course.id
                ).exists()
            ):
                raise PermissionDenied(
                    (
                        "Teacher is not assigned "
                        "to this course."
                    )
                )

            auditorium = serializer.validated_data.get(
                "auditorium"
            )
            if (
                auditorium
                and auditorium.company
                != user.company
            ):
                raise PermissionDenied(
                    (
                        "Auditorium must belong "
                        "to the same company."
                    )
                )

            students = serializer.validated_data.get(
                "student_ids",
                [],
            )
            for student in students:
                if student.company != user.company:
                    raise PermissionDenied(
                        (
                            "Student must belong "
                            "to the same company."
                        )
                    )

        lessons_per_month = (
            serializer.validated_data.get(
                "lessons_per_month"
            )
        )
        total_months = (
            serializer.validated_data.get(
                "total_months"
            )
        )

        if lessons_per_month and total_months:
            serializer.validated_data[
                "lessons_count"
            ] = (
                lessons_per_month
                * total_months
            )

        schedule_days = (
            serializer.validated_data.get(
                "schedule_days",
                "",
            )
        )
        if not schedule_days:
            raise PermissionDenied(
                "Укажите дни занятий."
            )

        end_date = compute_group_end_date(
            serializer.validated_data.get(
                "start_date"
            ),
            schedule_days,
            serializer.validated_data.get(
                "lessons_count"
            ),
        )

        serializer.validated_data[
            "end_date"
        ] = end_date

        ensure_resource_available(
            serializer=serializer,
            resource="auditorium",
        )
        ensure_resource_available(
            serializer=serializer,
            resource="teacher",
        )

        teacher = serializer.validated_data.get(
            "teacher"
        )
        teacher_percent = (
            serializer.validated_data.get(
                "teacher_percent",
                0,
            )
            or 0
        )

        save_kwargs = {
            "company": user.company,
            "end_date": end_date,
            "teacher_percent": teacher_percent,
        }

        if teacher:
            save_kwargs[
                "status"
            ] = Group.Status.PENDING

        serializer.save(**save_kwargs)

        self._credit_teacher_percent_on_create(
            serializer.instance,
            teacher=teacher,
            course=course,
            teacher_percent=teacher_percent,
        )

        self._create_group_months(
            serializer.instance,
            total_months or 0,
        )

        self._create_contracts(
            serializer.instance,
            user=user,
            course=course,
            students=(
                serializer.validated_data.get(
                    "student_ids",
                    [],
                )
            ),
        )

        if teacher:
            self._notify_teacher(
                serializer.instance
            )

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        teacher_changed = False

        old_teacher_percent = (
            instance.teacher_percent
        )
        old_course = instance.course

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if (
                user.role == User.Role.MANAGER
                and "is_login_allowed"
                in serializer.validated_data
            ):
                raise PermissionDenied(
                    (
                        "Managers cannot change "
                        "group login access."
                    )
                )

            course = serializer.validated_data.get(
                "course",
                None,
            )
            if course:
                allowed = course.admins.filter(
                    id=user.id
                ).exists()

                if user.role == User.Role.MANAGER:
                    allowed = course.admins.filter(
                        company=user.company
                    ).exists()

                if not allowed:
                    raise PermissionDenied(
                        "Not allowed for this course."
                    )

            selected_teacher = (
                serializer.validated_data.get(
                    "teacher",
                    instance.teacher,
                )
            )
            if (
                selected_teacher
                and selected_teacher.company
                != user.company
            ):
                raise PermissionDenied(
                    (
                        "Teacher must belong to "
                        "the same company."
                    )
                )

            course_for_teacher = (
                course
                or instance.course
            )
            if (
                selected_teacher
                and course_for_teacher
                and not selected_teacher.teaching_courses.filter(
                    id=course_for_teacher.id
                ).exists()
            ):
                raise PermissionDenied(
                    (
                        "Teacher is not assigned "
                        "to this course."
                    )
                )

            auditorium = serializer.validated_data.get(
                "auditorium"
            )
            if (
                auditorium
                and auditorium.company
                != user.company
            ):
                raise PermissionDenied(
                    (
                        "Auditorium must belong "
                        "to the same company."
                    )
                )

            students = serializer.validated_data.get(
                "student_ids",
                [],
            )
            for student in students:
                if student.company != user.company:
                    raise PermissionDenied(
                        (
                            "Student must belong "
                            "to the same company."
                        )
                    )

            if (
                "teacher"
                in serializer.validated_data
                and serializer.validated_data[
                    "teacher"
                ]
                != instance.teacher
            ):
                teacher_changed = True

        ensure_resource_available(
            serializer=serializer,
            instance=instance,
            resource="auditorium",
        )
        ensure_resource_available(
            serializer=serializer,
            instance=instance,
            resource="teacher",
        )

        start_date = serializer.validated_data.get(
            "start_date",
            instance.start_date,
        )
        schedule_days = serializer.validated_data.get(
            "schedule_days",
            instance.schedule_days,
        )

        lessons_per_month = (
            serializer.validated_data.get(
                "lessons_per_month"
            )
        )
        total_months = (
            serializer.validated_data.get(
                "total_months"
            )
        )

        if lessons_per_month and total_months:
            total_lessons = (
                lessons_per_month
                * total_months
            )
            serializer.validated_data[
                "lessons_count"
            ] = total_lessons
            lessons_count = total_lessons
        else:
            lessons_count = (
                serializer.validated_data.get(
                    "lessons_count",
                    instance.lessons_count,
                )
            )

        end_date = compute_group_end_date(
            start_date,
            schedule_days,
            lessons_count,
        )

        save_kwargs = {
            "end_date": end_date
        }

        if (
            teacher_changed
            and instance.status
            != Group.Status.PENDING
        ):
            save_kwargs[
                "status"
            ] = Group.Status.PENDING

        serializer.save(**save_kwargs)

        if (
            "total_months"
            in serializer.validated_data
            or "lessons_per_month"
            in serializer.validated_data
        ):
            final_total_months = (
                total_months
                or instance.total_months
            )
            self._create_group_months(
                instance,
                final_total_months or 0,
            )

        if (
            "teacher"
            in serializer.validated_data
            or "course"
            in serializer.validated_data
            or "teacher_percent"
            in serializer.validated_data
        ):
            self._credit_teacher_percent(
                instance,
                teacher_changed=teacher_changed,
                old_percent=old_teacher_percent,
                old_course=old_course,
            )

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot delete groups."
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def resubmit_after_rejection(
        self,
        request,
        pk=None,
    ):
        user = request.user

        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                (
                    "Только курс-админ или менеджер "
                    "может повторить отправку."
                )
            )

        group = self.get_object()

        if group.status != Group.Status.REJECTED:
            return Response(
                {
                    "detail": (
                        "Можно повторить отправку только "
                        "для отклонённых групп."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not group.teacher:
            return Response(
                {
                    "detail": (
                        "У группы должен быть "
                        "назначен учитель."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.status = Group.Status.PENDING
        group.save()

        self._notify_teacher(group)

        return Response(
            {
                "detail": (
                    "Запрос повторно отправлен учителю."
                ),
                "status": group.status,
            }
        )

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
