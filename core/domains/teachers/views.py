from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import User
from core.permissions import IsCourseAdminOrManagerReadOnly
from core.domains.users.serializers import (
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    UserSerializer,
)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        role=User.Role.TEACHER
    ).order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [
        IsCourseAdminOrManagerReadOnly
    ]

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .prefetch_related("teaching_courses")
        )
        user = self.request.user

        if (
            user.is_authenticated
            and user.role in (
                User.Role.COURSE_ADMIN,
                User.Role.MANAGER,
            )
        ):
            if user.company:
                queryset = queryset.filter(
                    company=user.company
                )
            else:
                queryset = queryset.none()

        course_param = (
            self.request.query_params.get(
                "course"
            )
        )
        if course_param:
            try:
                course_id = int(course_param)
            except (TypeError, ValueError):
                return queryset.none()

            queryset = queryset.filter(
                teaching_courses__id=course_id
            )

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        user = request.user

        if user.role == User.Role.ADMIN:
            raise PermissionDenied(
                "Admins cannot create teachers."
            )

        if user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot create teachers."
            )

        serializer = TeacherCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(
            raise_exception=True
        )
        teacher = serializer.save()

        return Response(
            UserSerializer(teacher).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        user = self.request.user

        if user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot update teachers."
            )

        if user.role == User.Role.COURSE_ADMIN:
            if (
                "role"
                in serializer.validated_data
                and serializer.validated_data[
                    "role"
                ]
                != User.Role.TEACHER
            ):
                raise PermissionDenied(
                    (
                        "Course admins cannot "
                        "change roles."
                    )
                )

        if (
            "company"
            in serializer.validated_data
            and serializer.validated_data.get(
                "company"
            )
            != user.company
        ):
            raise PermissionDenied(
                "Not allowed for this company."
            )

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if request.user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot delete teachers."
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    def get_serializer_class(self):
        if self.action in (
            "update",
            "partial_update",
        ):
            return TeacherUpdateSerializer

        return super().get_serializer_class()
