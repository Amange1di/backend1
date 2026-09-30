import re

from django.contrib.auth import authenticate
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from core.models import Company, Course, User
from core.domains.users.passwords import validate_strong_password

class RegisterSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=200,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "company_name",
            "password",
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "company",
            "company_id",
            "max_managers",
            "max_pages",
            "max_blocks",
            "role",
        )

    def validate_username(self, value):
        candidate = value.strip()
        if User.objects.filter(
            username__iexact=candidate
        ).exists():
            raise serializers.ValidationError(
                _("A user with that username already exists.")
            )
        return candidate

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate_role(self, value):
        if isinstance(value, str):
            return value.lower()
        return value

    def validate_max_pages(self, value):
        if value in (None, ""):
            return 1
        if value < 1:
            raise serializers.ValidationError(
                _("Pages limit must be at least 1.")
            )
        return value

    def validate_max_blocks(self, value):
        if value in (None, ""):
            return 7
        if value < 1:
            raise serializers.ValidationError(
                _("Blocks limit must be at least 1.")
            )
        return value

    def create(self, validated_data):
        forced_role = (
            validated_data.pop(
                "force_role",
                None,
            )
            or self.context.get(
                "force_role"
            )
        )
        role = (
            forced_role
            or validated_data.get(
                "role",
                User.Role.TEACHER,
            )
        )
        created_by = validated_data.pop(
            "created_by",
            None,
        )
        company = validated_data.pop(
            "company",
            None,
        )
        validated_data.pop(
            "company_name",
            None,
        )

        user = User(
            username=validated_data[
                "username"
            ],
            first_name=validated_data.get(
                "first_name",
                "",
            ),
            last_name=validated_data.get(
                "last_name",
                "",
            ),
            phone=validated_data.get(
                "phone",
                "",
            ),
            address=validated_data.get(
                "address",
                "",
            ),
            telegram=validated_data.get(
                "telegram",
                "",
            ),
            company=company,
            max_managers=(
                validated_data.get(
                    "max_managers",
                    0,
                )
                or 0
            ),
            max_pages=(
                validated_data.get(
                    "max_pages",
                    1,
                )
                or 1
            ),
            max_blocks=(
                validated_data.get(
                    "max_blocks",
                    7,
                )
                or 7
            ),
            created_by=created_by,
            role=role,
        )
        user.set_password(
            validated_data["password"]
        )
        user.save()
        return user

class TeacherCreateSerializer(serializers.Serializer):
    username = serializers.CharField(
        validators=[UnicodeUsernameValidator()],
    )
    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    phone = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    email = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=254,
    )
    salary_rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    working_hours = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    color = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    address = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    telegram = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    course_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        allow_empty=False,
    )

    def validate_username(self, value):
        candidate = value.strip()
        if User.objects.filter(
            username__iexact=candidate
        ).exists():
            raise serializers.ValidationError(
                _(
                    "A user with that username already exists."
                )
            )
        return candidate

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate_color(self, value):
        if not value:
            return "#45B2EF"
        candidate = value.strip()
        if not re.match(
            r"^#[0-9A-Fa-f]{6}$",
            candidate,
        ):
            raise serializers.ValidationError(
                _(
                    "Color must be a HEX value like #3f51b5."
                )
            )
        return candidate

    def validate_course_ids(self, courses):
        request = self.context.get("request")
        user = (
            request.user
            if request
            else None
        )
        if not user:
            return courses

        if user.role == User.Role.COURSE_ADMIN:
            for course in courses:
                if not course.admins.filter(
                    id=user.id
                ).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )

        elif user.role == User.Role.MANAGER:
            for course in courses:
                if (
                    user.company
                    and not course.admins.filter(
                        company=user.company
                    ).exists()
                ):
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )

        return courses

    def create(self, validated_data):
        courses = validated_data.pop(
            "course_ids",
            [],
        )
        request = self.context.get("request")
        creator = (
            request.user
            if request
            else None
        )
        company = (
            creator.company
            if creator
            else None
        )

        teacher = User(
            username=validated_data[
                "username"
            ],
            email=validated_data.get(
                "email",
                "",
            ),
            first_name=validated_data.get(
                "first_name",
                "",
            ),
            last_name=validated_data.get(
                "last_name",
                "",
            ),
            phone=validated_data.get(
                "phone",
                "",
            ),
            address=validated_data.get(
                "address",
                "",
            ),
            telegram=validated_data.get(
                "telegram",
                "",
            ),
            salary_rate=validated_data.get(
                "salary_rate"
            ),
            working_hours=validated_data.get(
                "working_hours",
                "",
            ),
            color=validated_data.get(
                "color",
                "#45B2EF",
            ),
            company=company,
            created_by=creator,
            role=User.Role.TEACHER,
        )
        teacher.set_password(
            validated_data["password"]
        )
        teacher.save()

        if courses:
            teacher.teaching_courses.set(
                courses
            )

        return teacher

class TeacherUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    email = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=254,
    )
    course_ids = serializers.PrimaryKeyRelatedField(
        source="teaching_courses",
        many=True,
        queryset=Course.objects.all(),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "salary_rate",
            "working_hours",
            "color",
            "password",
            "course_ids",
        )

    def validate_password(self, value):
        if not value:
            return value
        return validate_strong_password(value, user=self.instance)

    def validate_color(self, value):
        if not value:
            return "#45B2EF"
        candidate = value.strip()
        if not re.match(
            r"^#[0-9A-Fa-f]{6}$",
            candidate,
        ):
            raise serializers.ValidationError(
                _(
                    "Color must be a HEX value like #3f51b5."
                )
            )
        return candidate

    def validate_course_ids(self, courses):
        request = self.context.get("request")
        user = (
            request.user
            if request
            else None
        )
        if not user:
            return courses

        if user.role == User.Role.COURSE_ADMIN:
            for course in courses:
                if not course.admins.filter(
                    id=user.id
                ).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )

        elif user.role == User.Role.MANAGER:
            for course in courses:
                if (
                    user.company
                    and not course.admins.filter(
                        company=user.company
                    ).exists()
                ):
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )

        return courses

    def update(
        self,
        instance,
        validated_data,
    ):
        password = validated_data.pop(
            "password",
            None,
        )
        teacher = super().update(
            instance,
            validated_data,
        )
        if password:
            teacher.set_password(password)
            teacher.save(
                update_fields=["password"]
            )
            Token.objects.filter(
                user=teacher
            ).delete()
        return teacher

class CourseAdminUpdateSerializer(
    serializers.ModelSerializer
):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "company",
            "company_id",
            "is_student_cabinet_enabled",
            "is_active",
            "max_managers",
            "max_pages",
            "max_blocks",
            "password",
        )

    def validate_password(self, value):
        if not value:
            return value
        return validate_strong_password(value, user=self.instance)

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

    def validate_max_pages(self, value):
        if value < 1:
            raise serializers.ValidationError(
                _("Pages limit must be at least 1.")
            )
        return value

    def validate_max_blocks(self, value):
        if value < 1:
            raise serializers.ValidationError(
                _("Blocks limit must be at least 1.")
            )
        return value

