from rest_framework import serializers

from core.models import (
    Company,
    Group,
    Student,
    User,
)

from .services import normalize_phone, sync_student_user


class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    one_time_password = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Group.objects.filter(archived_at__isnull=True),
        required=False,
    )
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
    )
    company_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Student
        fields = (
            "id",
            "username",
            "one_time_password",
            "user",
            "first_name",
            "last_name",
            "phone",
            "telegram",
            "company",
            "company_id",
            "can_login",
            "primary_course",
            "group_ids",
            "groups",
            "notes",
            "created_at",
        )
        read_only_fields = (
            "user",
            "company",
            "company_id",
            "username",
            "one_time_password",
        )

    def get_one_time_password(self, obj):
        # The plain one-time password exists only in memory immediately after
        # a brand-new student account is created. Existing cross-company
        # accounts never receive a new password, so nothing sensitive from
        # another company is exposed.
        return getattr(
            obj,
            "_one_time_password",
            None,
        )

    def validate_phone(self, value):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return value

        company = request.user.company
        if not company:
            return value

        normalized = normalize_phone(value)
        if not normalized:
            return value

        queryset = Student.objects.filter(
            company=company,
            archived_at__isnull=True,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        for phone in queryset.values_list("phone", flat=True).iterator():
            if normalize_phone(phone) == normalized:
                raise serializers.ValidationError(
                    "Студент с таким телефоном уже есть в вашей компании."
                )

        return value

    def create(self, validated_data):
        group_ids = validated_data.pop(
            "group_ids",
            [],
        )
        student = super().create(
            validated_data
        )

        if group_ids:
            student.groups.set(group_ids)

        request = self.context.get("request")
        sync_student_user(
            student,
            created_by=(
                request.user
                if request
                else None
            ),
        )
        return student

    def update(
        self,
        instance,
        validated_data,
    ):
        group_ids = validated_data.pop(
            "group_ids",
            None,
        )
        student = super().update(
            instance,
            validated_data,
        )

        if group_ids is not None:
            student.groups.set(group_ids)

        request = self.context.get("request")
        sync_student_user(
            student,
            created_by=(
                request.user
                if request
                else None
            ),
        )
        return student


class TransferGroupSerializer(serializers.Serializer):
    new_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.filter(archived_at__isnull=True)
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
    )
