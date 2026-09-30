from rest_framework import serializers

from core.models import (
    Company,
    StudentApplication,
    TeacherApplication,
)


class TeacherApplicationSerializer(
    serializers.ModelSerializer
):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TeacherApplication
        fields = (
            "id",
            "full_name",
            "phone",
            "email",
            "experience",
            "specialization",
            "expected_salary",
            "education",
            "about",
            "availability",
            "format",
            "company",
            "company_id",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "created_at",
            "updated_at",
        )


class StudentApplicationSerializer(
    serializers.ModelSerializer
):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = StudentApplication
        fields = (
            "id",
            "full_name",
            "phone",
            "email",
            "age",
            "course_interest",
            "experience_level",
            "learning_goal",
            "budget",
            "schedule_preference",
            "source",
            "company",
            "company_id",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "created_at",
            "updated_at",
        )
