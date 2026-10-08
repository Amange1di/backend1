from django.db import models
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.audit import write_audit
from core.models import (
    Group,
    Student,
    User,
)
from core.permissions import IsCourseAdminOrTeacherReadOnly

from .serializers import GroupSerializer
from .lifecycle import GroupLifecycleMixin
from .services import (
    compute_group_end_date,
    ensure_group_schedule_available,
)


class GroupViewSet(GroupLifecycleMixin, viewsets.ModelViewSet):
    queryset = (
        Group.objects.filter(
            archived_at__isnull=True
        )
        .select_related(
            "course",
            "teacher",
            "auditorium",
            "company",
        )
        .prefetch_related(
            Prefetch(
                "students",
                queryset=(
                    Student.objects.filter(archived_at__isnull=True)
                    .select_related("user", "company", "primary_course")
                    .prefetch_related("groups")
                ),
            )
        )
        .order_by("-created_at")
    )
    serializer_class = GroupSerializer
    permission_classes = [
        IsCourseAdminOrTeacherReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        selected_branch = self.request.COOKIES.get("eduosh_branch")
        if selected_branch and selected_branch.isdigit():
            queryset = queryset.filter(branch_id=int(selected_branch))

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
                    "course_access_denied"
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
                    "course_access_denied"
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
                        "teacher_company_mismatch"
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
                        "teacher_not_assigned_to_course"
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
                        "auditorium_company_mismatch"
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
                            "student_company_mismatch"
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
                "schedule_days_required"
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

        ensure_group_schedule_available(
            serializer=serializer,
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

        branch = serializer.validated_data.get("branch")
        if not branch or branch.company_id != user.company_id:
            raise PermissionDenied("branch_access_denied")
        if user.branches.exists() and not user.branches.filter(id=branch.id).exists():
            raise PermissionDenied("branch_access_denied")

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
                        "manager_group_login_access_forbidden"
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
                        "course_access_denied"
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
                        "teacher_company_mismatch"
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
                        "teacher_not_assigned_to_course"
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
                        "auditorium_company_mismatch"
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
                            "student_company_mismatch"
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

        serializer.validated_data[
            "end_date"
        ] = end_date

        ensure_group_schedule_available(
            serializer=serializer,
            instance=instance,
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
                "manager_group_archive_forbidden"
            )

        group = self.get_object()
        group.archived_at = timezone.now()
        group.save(update_fields=["archived_at"])

        write_audit(
            request,
            action="group.archived",
            obj=group,
            company=group.company,
            after={
                "archived_at": group.archived_at.isoformat(),
            },
        )

        return Response(status=204)

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
                    "group_resubmit_staff_only"
                )
            )

        group = self.get_object()

        if group.status != Group.Status.REJECTED:
            return Response(
                {
                    "detail": (
                        "group_resubmit_rejected_only"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not group.teacher:
            return Response(
                {
                    "detail": (
                        "group_teacher_required"
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
                    "group_resubmitted_to_teacher"
                ),
                "status": group.status,
            }
        )
