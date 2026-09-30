from rest_framework import serializers

from core.models import (
    Company,
    Group,
    Student,
    User,
)

from .services import sync_student_user


class StudentSerializer(serializers.ModelSerializer):
    setup_code = serializers.SerializerMethodField()
    setup_code_expires_at = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            role=User.Role.STUDENT
        ),
        required=False,
        allow_null=True,
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Group.objects.all(),
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
            "setup_code",
            "setup_code_expires_at",
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
            "company",
            "company_id",
            "setup_code",
            "setup_code_expires_at",
        )

    def get_setup_code(self, obj):
        return getattr(
            obj,
            "_setup_code",
            None,
        )

    def get_setup_code_expires_at(self, obj):
        value = getattr(
            obj,
            "_setup_code_expires_at",
            None,
        )
        return value.isoformat() if value else None

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
        queryset=Group.objects.all()
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
    )
