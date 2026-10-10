from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Branch, User
from core.domains.users.serializers import RegisterSerializer, UserSerializer
from .serializers import BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.company_id:
            return Branch.objects.none()
        qs = Branch.objects.filter(company_id=user.company_id)
        if user.role == User.Role.COMPANY_OWNER:
            return qs
        return qs.filter(users=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != User.Role.COMPANY_OWNER:
            raise PermissionDenied("branch_access_denied")
        serializer.save(company=user.company)

    def perform_update(self, serializer):
        if self.request.user.role != User.Role.COMPANY_OWNER:
            raise PermissionDenied("branch_access_denied")
        serializer.save()

    def perform_destroy(self, instance):
        # Archiving enforces group and main-branch invariants; hard delete is unsafe.
        raise PermissionDenied("branch_delete_not_allowed")

    @action(detail=True, methods=["post"], url_path="create-admin")
    def create_admin(self, request, pk=None):
        branch = self.get_object()
        if request.user.role != User.Role.COMPANY_OWNER:
            raise PermissionDenied("branch_access_denied")
        if branch.users.filter(role=User.Role.COURSE_ADMIN, is_active=True).exists():
            return Response({"code": "branch_admin_exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(
            data=request.data,
            context={"force_role": User.Role.COURSE_ADMIN},
        )
        serializer.is_valid(raise_exception=True)
        admin = serializer.save(
            created_by=request.user,
            company=request.user.company,
        )
        admin.branches.add(branch)
        return Response(
            {
                "user": UserSerializer(admin).data,
                "one_time_password": getattr(admin, "_one_time_password", None),
                "requires_password_setup": True,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        branch = self.get_object()
        if request.user.role != User.Role.COMPANY_OWNER:
            raise PermissionDenied("branch_access_denied")
        if branch.is_main:
            return Response({"code": "cannot_archive_main_branch"}, status=status.HTTP_400_BAD_REQUEST)
        if branch.groups.filter(archived_at__isnull=True).exists():
            return Response({"code": "branch_has_active_groups"}, status=status.HTTP_400_BAD_REQUEST)
        branch.is_active = False
        branch.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(branch).data)
