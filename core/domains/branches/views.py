from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Branch, User
from .serializers import BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.company_id:
            return Branch.objects.none()
        qs = Branch.objects.filter(company_id=user.company_id)
        if user.role in (User.Role.COURSE_ADMIN, User.Role.ADMIN):
            return qs
        return qs.filter(users=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in (User.Role.COURSE_ADMIN, User.Role.ADMIN):
            raise PermissionDenied("branch_access_denied")
        serializer.save(company=user.company)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        branch = self.get_object()
        if request.user.role not in (User.Role.COURSE_ADMIN, User.Role.ADMIN):
            raise PermissionDenied("branch_access_denied")
        if branch.is_main:
            return Response({"code": "cannot_archive_main_branch"}, status=status.HTTP_400_BAD_REQUEST)
        if branch.groups.filter(archived_at__isnull=True).exists():
            return Response({"code": "branch_has_active_groups"}, status=status.HTTP_400_BAD_REQUEST)
        branch.is_active = False
        branch.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(branch).data)
