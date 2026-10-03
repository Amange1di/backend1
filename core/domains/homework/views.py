from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.models import (
    HomeworkSubmission,
    HomeworkTask,
    HomeworkTaskAttachment,
    User,
)

from .serializers import (
    HomeworkSubmissionSerializer,
    HomeworkTaskSerializer,
)
from .services import (
    is_submission_locked,
    student_can_access_task,
)


class HomeworkTaskViewSet(viewsets.ModelViewSet):
    queryset = (
        HomeworkTask.objects.all()
        .select_related("group", "teacher")
        .prefetch_related(
            "attachments",
            "students",
            "submissions",
        )
        .order_by("-created_at")
    )
    serializer_class = HomeworkTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            now = timezone.now()
            return (
                queryset.filter(is_published=True)
                .filter(
                    models.Q(publish_at__isnull=True)
                    | models.Q(publish_at__lte=now)
                )
                .filter(
                    models.Q(
                        target_type=HomeworkTask.TargetType.ALL_GROUP,
                        group__students__user=user,
                    )
                    | models.Q(
                        target_type=(
                            HomeworkTask.TargetType.SPECIFIC_STUDENTS
                        ),
                        students__user=user,
                    )
                )
                .distinct()
            )

        if (
            user.is_authenticated
            and user.role == User.Role.TEACHER
        ):
            return queryset.filter(teacher=user)

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            return queryset.filter(company=user.company)

        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.TEACHER:
            raise PermissionDenied(
                "teacher_only"
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data.get("group")

        if not group or group.teacher_id != user.id:
            raise PermissionDenied(
                "homework_own_groups_only"
            )

        instance = serializer.save(
            teacher=user,
            company=user.company,
        )
        self._save_attachments(instance)
        self._sync_library_resources(instance)
        data = self.get_serializer(instance).data
        headers = self.get_success_headers(data)

        return Response(
            data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if user.role == User.Role.TEACHER:
            if instance.teacher_id != user.id:
                raise PermissionDenied(
                    "homework_access_denied"
                )
            group = serializer.validated_data.get(
                "group",
                instance.group,
            )
            if group.teacher_id != user.id:
                raise PermissionDenied(
                    "homework_own_groups_only"
                )
            updated = serializer.save()
            self._save_attachments(updated, replace=True)
            self._sync_library_resources(updated)
            return

        if user.role == User.Role.COURSE_ADMIN:
            if instance.company != user.company:
                raise PermissionDenied(
                    "homework_access_denied"
                )
            updated = serializer.save()
            self._save_attachments(updated, replace=True)
            self._sync_library_resources(updated)
            return

        raise PermissionDenied("access_denied")

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        if (
            user.role == User.Role.TEACHER
            and instance.teacher_id == user.id
        ):
            return super().destroy(
                request,
                *args,
                **kwargs,
            )

        if (
            user.role == User.Role.COURSE_ADMIN
            and instance.company == user.company
        ):
            return super().destroy(
                request,
                *args,
                **kwargs,
            )

        raise PermissionDenied(
            "homework_delete_forbidden"
        )

    def _sync_library_resources(self, instance: HomeworkTask):
        resources = []
        existing_files = set(
            instance.attachments.values_list("file", flat=True)
        )

        for item in instance.library_items.all():
            resources.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "type": item.type,
                    "url": item.url or "",
                    "has_file": bool(item.file),
                }
            )

            if item.file and item.file.name not in existing_files:
                HomeworkTaskAttachment.objects.create(
                    task=instance,
                    file=item.file.name,
                )
                existing_files.add(item.file.name)

        instance.library_resource_snapshots = resources
        instance.save(update_fields=("library_resource_snapshots",))

    def _save_attachments(
        self,
        instance: HomeworkTask,
        replace: bool = False,
    ):
        files = self.request.FILES.getlist("files")

        if replace:
            clear_files = self.request.data.get("clear_files")
            if str(clear_files).lower() in {
                "1",
                "true",
                "yes",
            }:
                instance.attachments.all().delete()

        for file_obj in files:
            HomeworkTaskAttachment.objects.create(
                task=instance,
                file=file_obj,
            )


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    queryset = (
        HomeworkSubmission.objects.all()
        .select_related(
            "task",
            "student",
            "student__user",
        )
        .order_by("-submitted_at")
    )
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_authenticated
            and user.role == User.Role.STUDENT
        ):
            return queryset.filter(student__user=user)

        if (
            user.is_authenticated
            and user.role == User.Role.TEACHER
        ):
            return queryset.filter(task__teacher=user)

        if (
            user.is_authenticated
            and user.role == User.Role.COURSE_ADMIN
        ):
            if user.company:
                return queryset.filter(
                    task__company=user.company
                )
            return queryset.none()

        if (
            user.is_authenticated
            and user.role == User.Role.MANAGER
        ):
            if user.company:
                return queryset.filter(
                    task__company=user.company
                )
            return queryset.none()

        return queryset.none()

    def create(self, request, *args, **kwargs):
        user = request.user

        if user.role != User.Role.STUDENT:
            raise PermissionDenied(
                "student_only"
            )

        student = getattr(
            user,
            "student_profile",
            None,
        )
        if not student:
            raise PermissionDenied(
                "student_profile_not_found"
            )

        task_id = request.data.get("task")
        task = get_object_or_404(
            HomeworkTask,
            pk=task_id,
        )

        if not student_can_access_task(task, student):
            raise PermissionDenied(
                "homework_submit_own_groups_only"
            )

        if is_submission_locked(task):
            raise PermissionDenied(
                "homework_deadline_passed"
            )

        if HomeworkSubmission.objects.filter(
            task=task,
            student=student,
        ).exists():
            raise PermissionDenied(
                "homework_submission_exists"
            )

        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(student=student)
        headers = self.get_success_headers(
            serializer.data
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if user.role == User.Role.STUDENT:
            if instance.student.user_id != user.id:
                raise PermissionDenied(
                    "homework_submission_access_denied"
                )

            allowed_fields = {
                "answer_text",
                "file",
            }
            update_fields = set(
                serializer.validated_data.keys()
            )
            if not update_fields.issubset(
                allowed_fields
            ):
                raise PermissionDenied(
                    "homework_student_update_restricted"
                )

            if is_submission_locked(instance.task):
                raise PermissionDenied(
                    "homework_deadline_passed"
                )

            serializer.save(
                status=HomeworkSubmission.Status.PENDING
            )
            return

        if user.role == User.Role.TEACHER:
            if instance.task.teacher_id != user.id:
                raise PermissionDenied(
                    "homework_submission_access_denied"
                )

            allowed_fields = {
                "status",
                "grade",
                "teacher_comment",
            }
            update_fields = set(
                serializer.validated_data.keys()
            )
            if not update_fields.issubset(
                allowed_fields
            ):
                raise PermissionDenied(
                    "homework_teacher_review_only"
                )

            serializer.save()
            return

        raise PermissionDenied("access_denied")

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        if (
            user.role == User.Role.STUDENT
            and instance.student.user_id == user.id
        ):
            return super().destroy(
                request,
                *args,
                **kwargs,
            )

        if (
            user.role == User.Role.TEACHER
            and instance.task.teacher_id == user.id
        ):
            return super().destroy(
                request,
                *args,
                **kwargs,
            )

        raise PermissionDenied(
            "homework_submission_delete_forbidden"
        )
