from rest_framework import serializers

from core.models import (
    Company,
    StudentApplication,
    TeacherApplication,
)


class CompanyApplicationMixin:
    application_type = ""

    def _resolve_company(self, attrs):
        raw_company = self.initial_data.get("company_name")
        if not raw_company:
            return attrs

        company = None
        value = str(raw_company).strip()

        if value.isdigit():
            company = Company.objects.filter(pk=int(value)).first()

        if company is None:
            company = Company.objects.filter(name__iexact=value).first()

        if company is None:
            raise serializers.ValidationError(
                {"company_name": "Компания не найдена."}
            )

        attrs["company"] = company
        return attrs

    def validate(self, attrs):
        return self._resolve_company(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["type"] = self.application_type
        data["company_name"] = (
            instance.company.name
            if instance.company
            else ""
        )
        return data


class TeacherApplicationSerializer(
    CompanyApplicationMixin,
    serializers.ModelSerializer,
):
    application_type = "teacher"

    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
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
            "company_name",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "status",
            "created_at",
            "updated_at",
        )


class StudentApplicationSerializer(
    CompanyApplicationMixin,
    serializers.ModelSerializer,
):
    application_type = "student"

    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
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
            "company_name",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "status",
            "created_at",
            "updated_at",
        )
