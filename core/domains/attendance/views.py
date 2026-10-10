from datetime import date

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Attendance, Group, User
from core.permissions import (
    IsCourseAdminOrTeacherReadOnly,
    IsTeacherOrCourseAdminReadOnly,
)

from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by(
        "-created_at"
    )
    serializer_class = AttendanceSerializer
    permission_classes = [
        IsCourseAdminOrTeacherReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        selected_branch = self.request.COOKIES.get("eduosh_branch")
        if selected_branch and selected_branch.isdigit():
            queryset = queryset.filter(group__branch_id=int(selected_branch))

        if (
            user.is_authenticated
            and user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN)
        ):
            return queryset.filter(
                models.Q(
                    group__course__admins=user
                )
                | models.Q(
                    group__company=user.company
                )
            ).distinct()

        if (
            user.is_authenticated
            and user.role == User.Role.TEACHER
        ):
            return queryset.filter(
                group__teacher=user
            )

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            return queryset.filter(
                student__user=user
            )

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.role in (
            User.Role.COMPANY_OWNER,
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise PermissionDenied(
                (
                    "attendance_mark_staff_forbidden"
                )
            )

        group = serializer.validated_data.get(
            "group"
        )
        if (
            user.role == User.Role.TEACHER
            and group.teacher_id != user.id
        ):
            raise PermissionDenied(
                "group_access_denied"
            )

        serializer.save()


class AttendanceMarkView(APIView):
    permission_classes = [
        IsTeacherOrCourseAdminReadOnly
    ]

    @staticmethod
    def _parse_date(value):
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _ensure_access(user, group):
        if user.role == User.Role.MANAGER:
            raise permissions.PermissionDenied(
                "manager_access_denied"
            )

        if user.role == User.Role.STUDENT:
            raise permissions.PermissionDenied(
                "student_access_denied"
            )

        if user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            if user.role == User.Role.COURSE_ADMIN and not user.branches.filter(id=group.branch_id).exists():
                raise permissions.PermissionDenied("branch_access_denied")
            allowed = False

            if group.course:
                allowed = (
                    group.course.admins.filter(
                        id=user.id
                    ).exists()
                )

            if (
                group.company
                and group.company == user.company
            ):
                allowed = True

            if not allowed:
                raise permissions.PermissionDenied(
                    "course_access_denied"
                )

        if (
            user.role == User.Role.TEACHER
            and group.teacher_id != user.id
        ):
            raise permissions.PermissionDenied(
                "group_access_denied"
            )

    def get(self, request):
        group_id = request.query_params.get(
            "group"
        )
        date_str = request.query_params.get(
            "date"
        )

        if not group_id or not date_str:
            return Response(
                {
                    "detail": (
                        "attendance_group_date_required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = self._parse_date(date_str)
        if not target_date:
            return Response(
                {
                    "detail": (
                        "invalid_date_format"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(
            Group,
            pk=group_id,
        )
        self._ensure_access(
            request.user,
            group,
        )

        students = list(
            group.students.all().order_by(
                "first_name",
                "last_name",
            )
        )
        existing = Attendance.objects.filter(
            group=group,
            date=target_date,
        )
        status_map = {
            item.student_id: item.status
            for item in existing
        }

        return Response(
            {
                "group": {
                    "id": group.id,
                    "name": group.name,
                },
                "date": target_date.isoformat(),
                "students": [
                    {
                        "id": student.id,
                        "first_name": (
                            student.first_name
                        ),
                        "last_name": (
                            student.last_name
                        ),
                        "status": status_map.get(
                            student.id
                        ),
                    }
                    for student in students
                ],
            }
        )

    def post(self, request):
        if request.user.role in (
            User.Role.COMPANY_OWNER,
            User.Role.COURSE_ADMIN,
            User.Role.MANAGER,
        ):
            raise permissions.PermissionDenied(
                (
                    "attendance_mark_staff_forbidden"
                )
            )

        group_id = request.data.get("group")
        date_str = request.data.get("date")
        items = request.data.get(
            "items",
            [],
        )

        if not group_id or not date_str:
            return Response(
                {
                    "detail": (
                        "attendance_group_date_required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_date = self._parse_date(date_str)
        if not target_date:
            return Response(
                {
                    "detail": (
                        "invalid_date_format"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(
            Group,
            pk=group_id,
        )
        self._ensure_access(
            request.user,
            group,
        )

        if target_date > date.today():
            return Response(
                {"detail": "attendance_future_date_read_only"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = {
            student.id: student
            for student
            in group.students.all()
        }
        updated = []

        for item in items:
            student_id = item.get("student")
            status_value = item.get("status")

            if student_id not in students:
                continue

            if (
                status_value
                not in dict(
                    Attendance.Status.choices
                )
            ):
                continue

            record, _ = (
                Attendance.objects.update_or_create(
                    group=group,
                    student=students[
                        student_id
                    ],
                    date=target_date,
                    defaults={
                        "status": status_value
                    },
                )
            )
            updated.append(record)

        return Response(
            {
                "saved": len(updated),
                "date": target_date.isoformat(),
            }
        )
