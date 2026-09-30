from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import (
    Attendance,
    Course,
    Payment,
    Student,
    User,
)
from core.permissions import IsCourseAdminOrManagerReadOnly

from .serializers import CourseSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("-created_at")
    serializer_class = CourseSerializer
    permission_classes = [IsCourseAdminOrManagerReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            return queryset.filter(admins=user)

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if not user.company:
                return queryset.none()

            return queryset.filter(
                admins__company=user.company
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot create courses."
            )

        admins = serializer.validated_data.get(
            "admins",
            [],
        )

        if user.role == User.Role.COURSE_ADMIN:
            for admin in admins:
                if admin.company != user.company:
                    raise PermissionDenied(
                        (
                            "Course admins can only assign "
                            "their company admins."
                        )
                    )

            course = serializer.save()
            course.admins.add(user)

            if admins:
                course.admins.add(*admins)
            return

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user

        if user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot update courses."
            )

        if user.role == User.Role.COURSE_ADMIN:
            admins = serializer.validated_data.get(
                "admins",
                None,
            )

            if admins is not None:
                for admin in admins:
                    if admin.company != user.company:
                        raise PermissionDenied(
                            (
                                "Course admins can only assign "
                                "their company admins."
                            )
                        )

            course = serializer.save()
            course.admins.add(user)
            return

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot delete courses."
            )
        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        course = self.get_object()
        students_qs = Student.objects.filter(
            primary_course=course
        )
        students_count = students_qs.count()

        paid_students = (
            Payment.objects.filter(
                status=Payment.Status.PAID,
                student__in=students_qs,
            )
            .values("student")
            .distinct()
            .count()
        )

        attendance_qs = Attendance.objects.filter(
            group__course=course
        )
        total_attendance = attendance_qs.count()
        present_count = attendance_qs.filter(
            status=Attendance.Status.PRESENT
        ).count()
        excused_count = attendance_qs.filter(
            status=Attendance.Status.EXCUSED
        ).count()
        absent_count = attendance_qs.filter(
            status=Attendance.Status.ABSENT
        ).count()

        attendance_rate = (
            (
                present_count
                + excused_count
            )
            / total_attendance
            if total_attendance
            else 0
        )

        return Response(
            {
                "students_total": students_count,
                "students_paid": paid_students,
                "attendance_total": total_attendance,
                "attendance_present": present_count,
                "attendance_excused": excused_count,
                "attendance_absent": absent_count,
                "attendance_rate": round(
                    attendance_rate,
                    4,
                ),
            }
        )
