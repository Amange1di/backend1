import re

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Company, Course, User


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
        read_only_fields = ()

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


class RegisterSerializer(serializers.ModelSerializer):
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
        forced_role = self.context.get(
            "force_role"
        )
        role = (
            forced_role
            or validated_data.get(
                "role",
                User.Role.TEACHER,
            )
        )
        created_by = validated_data.get(
            "created_by"
        )
        company = validated_data.pop(
            "company",
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
        return user


class TeacherCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
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
        if User.objects.filter(
            username=value
        ).exists():
            raise serializers.ValidationError(
                _(
                    "A user with that username already exists."
                )
            )
        return value

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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError(
                _("Invalid credentials.")
            )
        attrs["user"] = user
        return attrs


class StudentIdentityLoginSerializer(
    serializers.Serializer
):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )


class StudentSetPasswordSerializer(
    serializers.Serializer
):
    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=6,
    )

    def validate(self, attrs):
        if (
            attrs["password"]
            != attrs["password_confirm"]
        ):
            raise serializers.ValidationError(
                {
                    "password_confirm": _(
                        "Passwords do not match."
                    )
                }
            )
        return attrs


class StudentProfileSerializer(
    serializers.Serializer
):
    phone = serializers.CharField(
        required=False,
        allow_blank=False,
    )
    telegram = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        trim_whitespace=False,
        min_length=6,
    )
