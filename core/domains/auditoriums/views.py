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
        selected_branch = self.request.COOKIES.get("eduosh_branch")
        if selected_branch and selected_branch.isdigit():
            queryset = queryset.filter(branch_id=int(selected_branch))

        if (
            user.is_authenticated
            and user.role in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN)
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

        branch = serializer.validated_data.get("branch")
        if not branch:
            selected_branch = self.request.COOKIES.get("eduosh_branch")
            allowed = user.company.branches.filter(is_active=True)
            if user.branches.exists():
                allowed = allowed.filter(users=user)
            if selected_branch and selected_branch.isdigit():
                branch = allowed.filter(id=int(selected_branch)).first()
            elif allowed.count() == 1:
                branch = allowed.first()
        if not branch or branch.company_id != user.company_id:
            raise PermissionDenied("branch_access_denied")
        if user.branches.exists() and not user.branches.filter(id=branch.id).exists():
            raise PermissionDenied("branch_access_denied")
        serializer.save(company=user.company, branch=branch)
