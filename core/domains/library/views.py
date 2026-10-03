from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.models import (
    Group,
    HomeworkTask,
    HomeworkTaskAttachment,
    LibraryFavorite,
    LibraryFolder,
    LibraryHomeworkTemplate,
    LibraryItem,
    User,
)

from .serializers import LibraryFolderSerializer, LibraryItemSerializer


ALLOWED_ROLES = {User.Role.COURSE_ADMIN, User.Role.MANAGER, User.Role.TEACHER}


class LibraryItemViewSet(viewsets.ModelViewSet):
    serializer_class = LibraryItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.role not in ALLOWED_ROLES or not user.company_id:
            return LibraryItem.objects.none()

        qs = (
            LibraryItem.objects.filter(company_id=user.company_id)
            .select_related("course", "folder", "created_by", "homework_template")
            .prefetch_related("favorites")
        )

        if user.role == User.Role.TEACHER:
            qs = qs.filter(created_by=user)

        if self.request.query_params.get("include_archived") != "true":
            qs = qs.exclude(status=LibraryItem.Status.ARCHIVED)

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                models.Q(title__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(created_by__first_name__icontains=search)
                | models.Q(created_by__last_name__icontains=search)
                | models.Q(course__title__icontains=search)
            )

        for param, field in (("type", "type"), ("course", "course_id"), ("folder", "folder_id")):
            value = self.request.query_params.get(param)
            if value:
                qs = qs.filter(**{field: value})

        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(created_by=user)
        if self.request.query_params.get("favorite") == "true":
            qs = qs.filter(favorites__user=user)

        ordering = self.request.query_params.get("ordering", "-created_at")
        allowed = {"created_at", "-created_at", "title", "-title", "usage_count", "-usage_count"}
        return qs.order_by(ordering if ordering in allowed else "-created_at").distinct()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.COURSE_ADMIN, User.Role.TEACHER} or not user.company_id:
            raise PermissionDenied("library_create_forbidden")
        serializer.save(
            company=user.company,
            created_by=user,
            visibility=(
                LibraryItem.Visibility.PRIVATE
                if user.role == User.Role.TEACHER
                else serializer.validated_data.get(
                    "visibility",
                    LibraryItem.Visibility.PRIVATE,
                )
            ),
        )

    def perform_update(self, serializer):
        item = self.get_object()
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN and item.created_by_id != user.id:
            raise PermissionDenied("library_edit_forbidden")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        user = request.user
        if user.role != User.Role.COURSE_ADMIN and item.created_by_id != user.id:
            raise PermissionDenied("library_delete_forbidden")
        item.status = LibraryItem.Status.ARCHIVED
        item.archived_at = timezone.now()
        item.save(update_fields=("status", "archived_at", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk=None):
        item = self.get_object()
        if request.method == "POST":
            LibraryFavorite.objects.get_or_create(item=item, user=request.user)
        else:
            LibraryFavorite.objects.filter(item=item, user=request.user).delete()
        return Response({"favorite": request.method == "POST"})

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        source = self.get_object()
        data = self.get_serializer(source).data
        for key in ("id", "file_url", "favorite", "usage_count", "author_name", "course_name", "folder_name", "created_at", "updated_at"):
            data.pop(key, None)
        data["title"] = f"{source.title} — copy"
        data["course"] = source.course_id
        data["folder"] = source.folder_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        copy = serializer.save(company=request.user.company, created_by=request.user)
        if source.file:
            copy.file = source.file
            copy.save(update_fields=("file",))
        return Response(self.get_serializer(copy).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        item = self.get_object()
        user = request.user
        if user.role != User.Role.TEACHER:
            raise PermissionDenied("teacher_only")
        if item.type != LibraryItem.Type.HOMEWORK:
            raise ValidationError({"detail": "library_item_not_homework"})

        group_id = request.data.get("group_id")
        deadline = request.data.get("deadline")
        lesson_number = request.data.get("lesson_number")
        if not group_id or not deadline:
            raise ValidationError({"detail": "group_and_deadline_required"})

        group = Group.objects.filter(
            pk=group_id,
            company_id=user.company_id,
            teacher_id=user.id,
        ).first()
        if not group:
            raise PermissionDenied("homework_own_groups_only")

        template = getattr(item, "homework_template", None)
        with transaction.atomic():
            task = HomeworkTask.objects.create(
                group=group,
                teacher=user,
                company=user.company,
                lesson_number=lesson_number or None,
                title=item.title,
                description=(template.instruction if template and template.instruction else item.description),
                material_url=item.url or "",
                task_type=HomeworkTask.TaskType.HOMEWORK,
                deadline=deadline,
                is_published=True,
                library_item=item,
            )
            if item.file:
                HomeworkTaskAttachment.objects.create(
                    task=task,
                    file=item.file.name,
                )
            item.usage_count = models.F("usage_count") + 1
            item.save(update_fields=("usage_count", "updated_at"))
            item.refresh_from_db(fields=("usage_count",))
        from core.domains.homework.serializers import HomeworkTaskSerializer
        return Response(HomeworkTaskSerializer(task, context={"request": request}).data, status=status.HTTP_201_CREATED)


class LibraryFolderViewSet(viewsets.ModelViewSet):
    serializer_class = LibraryFolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in ALLOWED_ROLES or not user.company_id:
            return LibraryFolder.objects.none()
        qs = LibraryFolder.objects.filter(company_id=user.company_id).select_related("parent", "course")
        if user.role == User.Role.TEACHER:
            qs = qs.filter(created_by=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.COURSE_ADMIN, User.Role.TEACHER}:
            raise PermissionDenied("library_folder_create_forbidden")
        serializer.save(company=user.company, created_by=user)

    def perform_update(self, serializer):
        folder = self.get_object()
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN and folder.created_by_id != user.id:
            raise PermissionDenied("library_folder_edit_forbidden")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role != User.Role.COURSE_ADMIN and instance.created_by_id != user.id:
            raise PermissionDenied("library_folder_delete_forbidden")
        instance.delete()
