import re

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from core.models import User
from core.domains.users.passwords import validate_strong_password

class UserSerializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(
        source="created_by_id",
        read_only=True,
    )
    managers_count = serializers.SerializerMethodField(
        read_only=True,
    )
    course_ids = serializers.SerializerMethodField(
        read_only=True,
    )
    course_titles = serializers.SerializerMethodField(
        read_only=True,
    )
    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )
    company_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "salary_rate",
            "working_hours",
            "color",
            "company",
            "company_id",
            "company_name",
            "is_student_cabinet_enabled",
            "must_set_password",
            "created_by",
            "role",
            "is_active",
            "max_managers",
            "max_pages",
            "max_blocks",
            "managers_count",
            "course_ids",
            "course_titles",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "salary_rate",
            "working_hours",
            "color",
            "company",
            "company_id",
            "company_name",
            "is_student_cabinet_enabled",
            "must_set_password",
            "created_by",
            "role",
            "is_active",
            "max_managers",
            "max_pages",
            "max_blocks",
            "managers_count",
            "course_ids",
            "course_titles",
        )

    def get_managers_count(self, obj):
        if obj.role != User.Role.COURSE_ADMIN:
            return 0
        if not hasattr(
            obj,
            "get_managers_count",
        ):
            return 0
        return obj.get_managers_count()

    def get_course_ids(self, obj):
        if obj.role in (
            User.Role.COURSE_ADMIN,
            User.Role.TEACHER,
        ):
            return list(
                obj.teaching_courses.values_list(
                    "id",
                    flat=True,
                )
            )
        return []

    def get_course_titles(self, obj):
        if obj.role in (
            User.Role.COURSE_ADMIN,
            User.Role.TEACHER,
        ):
            return list(
                obj.teaching_courses.values_list(
                    "title",
                    flat=True,
                )
            )
        return []

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "password",
        )

    def validate_password(self, value):
        if not value:
            return value
        return validate_strong_password(
            value,
            user=self.instance,
        )

    def update(
        self,
        instance,
        validated_data,
    ):
        password = validated_data.pop(
            "password",
            None,
        )
        user = super().update(
            instance,
            validated_data,
        )
        if password:
            user.set_password(password)
            user.save(
                update_fields=["password"]
            )
            Token.objects.filter(
                user=user
            ).delete()
        return user

