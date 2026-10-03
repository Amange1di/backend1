from django.utils import timezone
from rest_framework import serializers

from core.models import (
    LibraryFavorite,
    LibraryFolder,
    LibraryHomeworkTemplate,
    LibraryItem,
)
from core.security import validate_upload


ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "png", "jpg", "jpeg", "webp", "zip",
}


class LibraryFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryFolder
        fields = ("id", "name", "course", "parent", "created_at")
        read_only_fields = ("created_at",)

    def validate_parent(self, parent):
        if not parent:
            return parent
        request = self.context["request"]
        if parent.company_id != request.user.company_id:
            raise serializers.ValidationError("invalid_folder")
        depth = 1
        current = parent
        while current.parent_id:
            depth += 1
            current = current.parent
            if depth >= 3:
                raise serializers.ValidationError("folder_depth_limit")
        return parent


class LibraryItemSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(source="course.title", read_only=True)
    folder_name = serializers.CharField(source="folder.name", read_only=True)
    file_url = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()
    instruction = serializers.CharField(source="homework_template.instruction", required=False, allow_blank=True)
    max_score = serializers.IntegerField(source="homework_template.max_score", required=False, min_value=0)
    default_deadline_days = serializers.IntegerField(source="homework_template.default_deadline_days", required=False, min_value=0)

    class Meta:
        model = LibraryItem
        fields = (
            "id", "title", "description", "type", "course", "course_name",
            "folder", "folder_name", "file", "file_url", "url", "tags",
            "visibility", "status", "usage_count", "author_name", "favorite",
            "instruction", "max_score", "default_deadline_days",
            "created_at", "updated_at",
        )
        read_only_fields = ("usage_count", "author_name", "favorite", "created_at", "updated_at")
        extra_kwargs = {"file": {"write_only": True, "required": False, "allow_null": True}}

    def get_author_name(self, obj):
        return (f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username)

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_favorite(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.favorites.filter(user=request.user).exists())

    def validate_file(self, value):
        return validate_upload(value, max_bytes=25 * 1024 * 1024, allowed_extensions=ALLOWED_EXTENSIONS)

    def validate_folder(self, folder):
        request = self.context["request"]
        if folder and folder.company_id != request.user.company_id:
            raise serializers.ValidationError("invalid_folder")
        return folder

    def validate_course(self, course):
        if not course:
            return course
        company = self.context["request"].user.company
        if not (
            course.groups.filter(company=company).exists()
            or course.admins.filter(company=company).exists()
        ):
            raise serializers.ValidationError("invalid_course")
        return course

    def validate(self, attrs):
        item_type = attrs.get("type", getattr(self.instance, "type", None))
        url = attrs.get("url", getattr(self.instance, "url", ""))
        if item_type in {LibraryItem.Type.LINK, LibraryItem.Type.VIDEO} and not url:
            raise serializers.ValidationError({"url": "required"})
        return attrs

    def _template_data(self, validated_data):
        return validated_data.pop("homework_template", {})

    def create(self, validated_data):
        template = self._template_data(validated_data)
        item = LibraryItem.objects.create(**validated_data)
        if item.type == LibraryItem.Type.HOMEWORK:
            LibraryHomeworkTemplate.objects.create(library_item=item, **template)
        return item

    def update(self, instance, validated_data):
        template = self._template_data(validated_data)
        instance = super().update(instance, validated_data)
        if instance.type == LibraryItem.Type.HOMEWORK:
            obj, _ = LibraryHomeworkTemplate.objects.get_or_create(library_item=instance)
            for key, value in template.items():
                setattr(obj, key, value)
            obj.save()
        return instance
