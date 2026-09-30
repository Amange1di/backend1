from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from core.models import Auditorium, User
from core.permissions import IsCourseAdminOrManagerReadOnly

from .serializers import AuditoriumSerializer


class AuditoriumViewSet(viewsets.ModelViewSet):
    queryset = Auditorium.objects.all().order_by(
        "-created_at"
    )
    serializer_class = AuditoriumSerializer
    permission_classes = [
        IsCourseAdminOrManagerReadOnly
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            if user.company:
                return queryset.filter(
                    company=user.company
                )
            return queryset.none()

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if user.company:
                return queryset.filter(
                    company=user.company
                )
            return queryset.none()

        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == User.Role.MANAGER:
            raise PermissionDenied(
                "Managers cannot create auditoriums."
            )

        serializer.save(
            company=user.company
        )
