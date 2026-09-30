from rest_framework import serializers

from core.models import Company, Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    created_by = serializers.IntegerField(
        source="created_by_id",
        read_only=True,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "assigned_to",
            "assigned_to_name",
            "due_date",
            "due_time",
            "status",
            "priority",
            "repeat_type",
            "is_seen",
            "created_by",
            "company",
            "company_id",
            "created_at",
        )
        read_only_fields = ()

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return ""
        full_name = (
            f"{obj.assigned_to.first_name} "
            f"{obj.assigned_to.last_name}"
        ).strip()
        return full_name or obj.assigned_to.username
