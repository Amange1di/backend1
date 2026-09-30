from django.db import models
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Student, User
from core.audit import write_audit
from core.permissions import (
    IsCourseAdminOrManagerOrStudentReadOnly,
)

from .serializers import (
    StudentSerializer,
    TransferGroupSerializer,
)
from .services import sync_student_user
from core.domains.auth.first_login import issue_first_login_password


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.filter(
        archived_at__isnull=True
    ).order_by("-created_at")
    serializer_class = StudentSerializer
    permission_classes = [
        IsCourseAdminOrManagerOrStudentReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            return queryset.filter(
                models.Q(
                    primary_course__admins=user
                )
                | models.Q(
                    groups__course__admins=user
                )
            ).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if not user.company:
                return queryset.none()

            return queryset.filter(
                models.Q(company=user.company)
                | models.Q(
                    primary_course__admins=user
                )
                | models.Q(
                    groups__company=user.company
                )
                | models.Q(
                    groups__course__admins=user
                )
            ).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            return queryset.filter(user=user)

        return queryset

    def _validate_course_access(
        self,
        *,
        user,
        course,
    ):
        if not course:
            return

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

    def _validate_group_access(
        self,
        *,
        user,
        groups,
    ):
        for group in groups:
            if group.course:
                allowed = group.course.admins.filter(
                    id=user.id
                ).exists()

                if user.role == User.Role.MANAGER:
                    allowed = (
                        group.course.admins.filter(
                            company=user.company
                        ).exists()
                    )

                if not allowed:
                    raise PermissionDenied(
                        "Not allowed for this group."
                    )

            elif (
                group.company
                and group.company != user.company
            ):
                raise PermissionDenied(
                    "Not allowed for this group."
                )

    @staticmethod
    def _auto_course_from_groups(
        course,
        groups,
    ):
        if course or not groups:
            return None

        first_course = groups[0].course
        if (
            first_course
            and all(
                group.course_id
                == first_course.id
                for group in groups
            )
        ):
            return first_course

        return None

    def perform_create(self, serializer):
        user = self.request.user

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            course = serializer.validated_data.get(
                "primary_course"
            )
            groups = serializer.validated_data.get(
                "group_ids",
                [],
            )
            account = serializer.validated_data.get(
                "user"
            )

            self._validate_course_access(
                user=user,
                course=course,
            )
            self._validate_group_access(
                user=user,
                groups=groups,
            )

            auto_course = (
                self._auto_course_from_groups(
                    course,
                    groups,
                )
            )

            if (
                account
                and account.company
                and account.company
                != user.company
            ):
                raise PermissionDenied(
                    "Not allowed for this user."
                )

            save_kwargs = {
                "company": user.company
            }

            if course:
                save_kwargs[
                    "primary_course"
                ] = course
            elif auto_course:
                save_kwargs[
                    "primary_course"
                ] = auto_course

            student = serializer.save(
                **save_kwargs
            )
            sync_student_user(
                student,
                created_by=user,
            )
            return

        student = serializer.save()
        sync_student_user(
            student,
            created_by=(
                user
                if user.is_authenticated
                else None
            ),
        )

    def perform_update(self, serializer):
        user = self.request.user

        if user.role in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            if (
                user.role == User.Role.MANAGER
                and "can_login"
                in serializer.validated_data
            ):
                raise PermissionDenied(
                    (
                        "Managers cannot change "
                        "student login access."
                    )
                )

            course = serializer.validated_data.get(
                "primary_course",
                None,
            )
            groups = serializer.validated_data.get(
                "group_ids",
                [],
            )

            self._validate_course_access(
                user=user,
                course=course,
            )
            self._validate_group_access(
                user=user,
                groups=groups,
            )

            auto_course = (
                self._auto_course_from_groups(
                    course,
                    groups,
                )
            )

            save_kwargs = {}
            if course:
                save_kwargs[
                    "primary_course"
                ] = course
            elif auto_course:
                save_kwargs[
                    "primary_course"
                ] = auto_course

            student = serializer.save(
                **save_kwargs
            )
            sync_student_user(
                student,
                created_by=user,
            )
            return

        student = serializer.save()
        sync_student_user(
            student,
            created_by=(
                user
                if user.is_authenticated
                else None
            ),
        )

    def destroy(self, request, *args, **kwargs):
        if request.user.role in (
            User.Role.MANAGER,
            User.Role.STUDENT,
        ):
            raise PermissionDenied(
                "Not allowed to archive students."
            )

        student = self.get_object()
        student.archived_at = timezone.now()
        student.can_login = False
        student.save(
            update_fields=[
                "archived_at",
                "can_login",
            ]
        )

        if student.user_id:
            student.user.is_active = False
            student.user.save(
                update_fields=["is_active"]
            )
            Token.objects.filter(
                user=student.user
            ).delete()

        write_audit(
            request,
            action="student.archived",
            obj=student,
            company=student.company,
            after={
                "archived_at": (
                    student.archived_at.isoformat()
                ),
                "can_login": False,
            },
        )

        return Response(status=204)

    @action(
        detail=True,
        methods=["post"],
        url_path="reset-password",
    )
    def reset_password(
        self,
        request,
        pk=None,
    ):
        if (
            request.user.role
            != User.Role.COURSE_ADMIN
        ):
            raise PermissionDenied(
                (
                    "Only course admins can reset "
                    "student passwords."
                )
            )

        student = self.get_object()

        if (
            student.company
            != request.user.company
        ):
            raise PermissionDenied(
                "Not allowed for this student."
            )

        if not student.user:
            sync_student_user(
                student,
                created_by=request.user,
            )
            student.refresh_from_db()

        Token.objects.filter(
            user=student.user
        ).delete()
        one_time_password = (
            issue_first_login_password(
                student.user
            )
        )

        return Response(
            {
                "detail": (
                    "Student password was reset."
                ),
                "must_set_password": True,
                "username": (
                    student.user.username
                ),
                "one_time_password": (
                    one_time_password
                ),
            }
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="transfer-group",
    )
    def transfer_group(
        self,
        request,
        pk=None,
    ):
        student = self.get_object()
        serializer = TransferGroupSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )

        new_group = serializer.validated_data[
            "new_group"
        ]
        note = serializer.validated_data.get(
            "note",
            "",
        )

        user = request.user
        if user.role not in (
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                (
                    "Only course admins and managers "
                    "can transfer students."
                )
            )

        if student.company != new_group.company:
            raise PermissionDenied(
                (
                    "Student and new group must "
                    "belong to the same company."
                )
            )

        if student.company != user.company:
            raise PermissionDenied(
                "Not allowed for this student."
            )

        if new_group.company != user.company:
            raise PermissionDenied(
                "Not allowed for this group."
            )

        student.groups.clear()
        student.groups.add(new_group)

        if new_group.course:
            student.primary_course = (
                new_group.course
            )

        if note:
            existing = student.notes or ""
            timestamp = timezone.now().strftime(
                "%d.%m.%Y %H:%M"
            )
            transfer_note = (
                f"[{timestamp}] Переведён в группу "
                f"«{new_group.name}». {note}"
            )
            student.notes = (
                f"{transfer_note}\n{existing}"
                if existing
                else transfer_note
            )

        student.save(
            update_fields=[
                "primary_course",
                "notes",
            ]
        )

        return Response(
            {
                "status": "ok",
                "detail": (
                    "Student transferred to group "
                    f"«{new_group.name}»."
                ),
            }
        )
