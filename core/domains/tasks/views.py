from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import Task, User
from core.permissions import IsCourseAdminOrManager

from .serializers import TaskSerializer
from .services import (
    build_task_instances,
    resolve_user_company_id,
)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
    permission_classes = [IsCourseAdminOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            if not user.company:
                return queryset.none()
            return queryset.filter(company=user.company)

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if not user.company:
                return queryset.none()
            return queryset.filter(
                assigned_to=user,
                company=user.company,
            )

        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied(
                "Only course admins can create tasks."
            )

        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        assigned_to = serializer.validated_data.get(
            "assigned_to"
        )
        if (
            not assigned_to
            or assigned_to.role != User.Role.MANAGER
        ):
            raise PermissionDenied(
                "Task must be assigned to a manager."
            )

        if (
            resolve_user_company_id(assigned_to)
            != resolve_user_company_id(user)
        ):
            raise PermissionDenied(
                "manager_company_mismatch"
            )

        tasks = build_task_instances(
            serializer.validated_data,
            user,
        )
        Task.objects.bulk_create(tasks)

        data = TaskSerializer(
            tasks,
            many=True,
        ).data
        return Response(
            data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        user = self.request.user

        if user.role == User.Role.MANAGER:
            if self.get_object().assigned_to_id != user.id:
                raise PermissionDenied(
                    "Not allowed for this task."
                )

            allowed_fields = {
                "status",
                "is_seen",
            }
            update_fields = set(
                serializer.validated_data.keys()
            )
            if not update_fields.issubset(
                allowed_fields
            ):
                raise PermissionDenied(
                    "Managers can only update status or seen flag."
                )

            serializer.save()
            return

        if user.role == User.Role.COURSE_ADMIN:
            assigned_to = serializer.validated_data.get(
                "assigned_to"
            )
            if (
                assigned_to
                and resolve_user_company_id(assigned_to)
                != resolve_user_company_id(user)
            ):
                raise PermissionDenied(
                    "manager_company_mismatch"
                )

            serializer.save()
            return

        raise PermissionDenied("access_denied")

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.COURSE_ADMIN:
            raise PermissionDenied(
                "course_admin_only"
            )
        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="mark-seen",
    )
    def mark_seen(self, request):
        user = request.user
        if user.role != User.Role.MANAGER:
            raise PermissionDenied(
                "manager_only"
            )

        data = request.data
        ids = []

        if isinstance(data, dict):
            ids = data.get("ids", []) or []
        elif isinstance(data, list):
            ids = data
        elif isinstance(data, str):
            raw = data.strip()
            if raw:
                if "," in raw:
                    ids = [
                        item.strip()
                        for item in raw.split(",")
                        if item.strip()
                    ]
                else:
                    ids = [raw]

        normalized_ids = []
        for item in ids:
            try:
                normalized_ids.append(int(item))
            except (TypeError, ValueError):
                continue

        queryset = self.get_queryset()
        if normalized_ids:
            queryset = queryset.filter(
                id__in=normalized_ids
            )

        updated = queryset.update(is_seen=True)
        return Response({"updated": updated})
