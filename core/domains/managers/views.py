from rest_framework.authtoken.models import Token
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.audit import write_audit
from core.models import Branch, User
from core.domains.auth.first_login import issue_first_login_password
from core.domains.users.serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class ManagerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        role=User.Role.MANAGER
    ).order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

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

    def create(self, request, *args, **kwargs):
        user = request.user

        if user.role not in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            raise PermissionDenied(
                (
                    "Only course admins can "
                    "create managers."
                )
            )

        if not user.can_create_manager():
            raise PermissionDenied(
                (
                    "Manager limit reached. "
                    f"Maximum: {user.max_managers}, "
                    f"Current: "
                    f"{user.get_managers_count()}"
                )
            )

        branch_ids = request.data.get("branch_ids")
        allowed_branches = Branch.objects.filter(company=user.company, is_active=True)
        if user.role != User.Role.COMPANY_OWNER and user.branches.exists():
            allowed_branches = allowed_branches.filter(users=user)
        if not branch_ids:
            selected_branch = request.COOKIES.get("eduosh_branch")
            if selected_branch and selected_branch.isdigit():
                branch_ids = [int(selected_branch)]
            elif allowed_branches.count() == 1:
                branch_ids = [allowed_branches.first().id]
            else:
                raise PermissionDenied("manager_branch_required")
        if not isinstance(branch_ids, list):
            raise PermissionDenied("manager_branch_required")
        branches = allowed_branches.filter(id__in=branch_ids)
        if branches.count() != len(set(branch_ids)):
            raise PermissionDenied("branch_access_denied")

        serializer = RegisterSerializer(
            data=request.data,
            context={
                "force_role": User.Role.MANAGER
            },
        )
        serializer.is_valid(
            raise_exception=True
        )
        manager = serializer.save(
            created_by=user,
            company=user.company,
        )
        manager.branches.set(branches)

        return Response(
            {
                "user": UserSerializer(manager).data,
                "one_time_password": getattr(
                    manager,
                    "_one_time_password",
                    None,
                ),
                "requires_password_setup": True,
            },
            status=status.HTTP_201_CREATED,
        )

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
        if request.user.role not in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            raise PermissionDenied(
                "Only course admins can reset manager passwords."
            )

        manager = self.get_object()
        Token.objects.filter(user=manager).delete()
        one_time_password = (
            issue_first_login_password(manager)
        )

        return Response(
            {
                "username": manager.username,
                "one_time_password": one_time_password,
                "requires_password_setup": True,
            }
        )

    def destroy(self, request, *args, **kwargs):
        manager = self.get_object()
        if request.user.role not in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            raise PermissionDenied(
                "Only course admins can deactivate managers."
            )

        manager.is_active = False
        manager.save(update_fields=["is_active"])
        Token.objects.filter(user=manager).delete()
        write_audit(
            request,
            action="manager.deactivated",
            obj=manager,
            company=manager.company,
            after={"is_active": False},
        )
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def get_serializer_class(self):
        if self.action in (
            "update",
            "partial_update",
        ):
            return UserUpdateSerializer

        return super().get_serializer_class()
