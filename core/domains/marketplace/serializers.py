from rest_framework import serializers

from core.models import Company, JobVacancy, PublicCourse
from core.security import validate_upload


class CompanySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "slug",
            "logo",
            "description",
            "category",
            "city",
            "district",
            "phone",
            "telegram",
            "whatsapp",
            "website",
            "rating",
            "reviews_count",
            "is_active",
            "owner",
        )
        read_only_fields = (
            "slug",
            "rating",
            "reviews_count",
        )


class PublicCourseSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )
    company_slug = serializers.CharField(
        source="company.slug",
        read_only=True,
    )
    landing_page_slug = serializers.SerializerMethodField()
    applications_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = PublicCourse
        fields = (
            "id",
            "company",
            "company_name",
            "company_slug",
            "landing_page_slug",
            "title",
            "slug",
            "price",
            "duration_weeks",
            "lesson_duration_minutes",
            "description",
            "category",
            "city",
            "schedule",
            "requirements",
            "curriculum",
            "rating",
            "reviews_count",
            "is_active",
            "is_promoted",
            "is_urgent",
            "image",
            "views",
            "applications_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "slug",
            "rating",
            "reviews_count",
            "views",
            "applications_count",
        )

    def validate_image(self, value):
        return validate_upload(
            value,
            max_bytes=5 * 1024 * 1024,
            allowed_extensions={"jpg", "jpeg", "png", "webp"},
        )

    def get_landing_page_slug(self, obj):
        if not obj.company:
            return None
        try:
            landing = obj.company.landing_pages.filter(
                status="active"
            ).first()
            return landing.slug if landing else None
        except Exception:
            return None


class JobVacancySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )
    company_slug = serializers.CharField(
        source="company.slug",
        read_only=True,
    )
    landing_page_slug = serializers.SerializerMethodField()
    applications_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = JobVacancy
        fields = (
            "id",
            "company",
            "company_name",
            "company_slug",
            "landing_page_slug",
            "title",
            "description",
            "category",
            "city",
            "district",
            "salary_min",
            "salary_max",
            "schedule",
            "requirements",
            "responsibilities",
            "is_active",
            "is_promoted",
            "is_urgent",
            "views",
            "applications_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "views",
            "applications_count",
        )

    def get_landing_page_slug(self, obj):
        if obj.company:
            landing = obj.company.landing_pages.filter(
                status="active"
            ).first()
            return landing.slug if landing else None
        return None


class JobVacancyDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )
    company_slug = serializers.CharField(
        source="company.slug",
        read_only=True,
    )
    company_phone = serializers.CharField(
        source="company.phone",
        read_only=True,
    )
    company_website = serializers.CharField(
        source="company.website",
        read_only=True,
    )
    applications_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = JobVacancy
        fields = (
            "id",
            "company",
            "company_name",
            "company_slug",
            "company_phone",
            "company_website",
            "title",
            "description",
            "category",
            "city",
            "district",
            "salary_min",
            "salary_max",
            "schedule",
            "requirements",
            "responsibilities",
            "is_active",
            "is_promoted",
            "is_urgent",
            "views",
            "applications_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "company",
            "views",
            "applications_count",
        )


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    def validate_logo(self, value):
        return validate_upload(
            value,
            max_bytes=5 * 1024 * 1024,
            allowed_extensions={"jpg", "jpeg", "png", "webp"},
        )

    class Meta:
        model = Company
        fields = (
            "name",
            "logo",
            "description",
            "category",
            "city",
            "district",
            "phone",
            "telegram",
            "whatsapp",
            "website",
        )
