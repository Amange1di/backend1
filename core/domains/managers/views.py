from rest_framework.authtoken.models import Token
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import User
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

    def create(self, request, *args, **kwargs):
        user = request.user

        if user.role != User.Role.COURSE_ADMIN:
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

        return Response(
            UserSerializer(manager).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        manager = self.get_object()
        if request.user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied(
                "Only course admins can deactivate managers."
            )

        manager.is_active = False
        manager.save(update_fields=["is_active"])
        Token.objects.filter(user=manager).delete()
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
