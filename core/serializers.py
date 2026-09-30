import re
import bleach

from django.contrib.auth import authenticate
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Attendance,
    Auditorium,
    Course,
    Expense,
    Group,
    GroupMonth,
    LandingHeaderLink,
    LandingPage,
    LandingSection,
    Payment,
    Student,
    TrialLead,
    Task,
    User,
    PromoCode,
    Company,
    PublicCourse,
    JobVacancy,
    StudentApplication,
    TeacherApplication,
)

from .domains.students.services import (
    normalize_phone,
    build_student_username,
    sync_student_user,
)


class UserSerializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    managers_count = serializers.SerializerMethodField(read_only=True)
    course_ids = serializers.SerializerMethodField(read_only=True)
    course_titles = serializers.SerializerMethodField(read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
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
        if not hasattr(obj, 'get_managers_count'):
            return 0
        return obj.get_managers_count()

    def get_course_ids(self, obj):
        if obj.role == User.Role.COURSE_ADMIN:
            return list(obj.teaching_courses.values_list("id", flat=True))
        if obj.role == User.Role.TEACHER:
            # Для преподавателей используем прямую связь teaching_courses
            return list(obj.teaching_courses.values_list("id", flat=True))
        return []

    def get_course_titles(self, obj):
        if obj.role == User.Role.COURSE_ADMIN:
            return list(obj.teaching_courses.values_list("title", flat=True))
        if obj.role == User.Role.TEACHER:
            # Для преподавателей используем прямую связь teaching_courses
            return list(obj.teaching_courses.values_list("title", flat=True))
        return []


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
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
            raise serializers.ValidationError(_("Pages limit must be at least 1."))
        return value

    def validate_max_blocks(self, value):
        if value in (None, ""):
            return 7
        if value < 1:
            raise serializers.ValidationError(_("Blocks limit must be at least 1."))
        return value

    def create(self, validated_data):
        forced_role = self.context.get("force_role")
        role = forced_role or validated_data.get("role", User.Role.TEACHER)
        created_by = validated_data.get("created_by")
        company = validated_data.pop("company", None)
        user = User(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            telegram=validated_data.get("telegram", ""),
            company=company,
            max_managers=validated_data.get("max_managers", 0) or 0,
            max_pages=validated_data.get("max_pages", 1) or 1,
            max_blocks=validated_data.get("max_blocks", 7) or 7,
            created_by=created_by,
            role=role,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "address", "telegram", "password")

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

class TeacherCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=True, allow_blank=False)
    email = serializers.CharField(required=False, allow_blank=True, max_length=254)
    salary_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    working_hours = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    telegram = serializers.CharField(required=False, allow_blank=True)
    course_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), allow_empty=False
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("A user with that username already exists."))
        return value

    def validate_color(self, value):
        if not value:
            return "#45B2EF"
        candidate = value.strip()
        if not re.match(r"^#[0-9A-Fa-f]{6}$", candidate):
            raise serializers.ValidationError(_("Color must be a HEX value like #3f51b5."))
        return candidate

    def validate_course_ids(self, courses):
        request = self.context.get("request")
        user = request.user if request else None
        if not user:
            return courses
        if user.role == User.Role.COURSE_ADMIN:
            for course in courses:
                if not course.admins.filter(id=user.id).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )
        elif user.role == User.Role.MANAGER:
            for course in courses:
                if user.company and not course.admins.filter(company=user.company).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )
        return courses

    def create(self, validated_data):
        courses = validated_data.pop("course_ids", [])
        request = self.context.get("request")
        creator = request.user if request else None
        company = creator.company if creator else None
        teacher = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            telegram=validated_data.get("telegram", ""),
            salary_rate=validated_data.get("salary_rate"),
            working_hours=validated_data.get("working_hours", ""),
            color=validated_data.get("color", "#45B2EF"),
            company=company,
            created_by=creator,
            role=User.Role.TEACHER,
        )
        teacher.set_password(validated_data["password"])
        teacher.save()
        if courses:
            teacher.teaching_courses.set(courses)
        return teacher

class TeacherUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True, max_length=254)
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
        if not re.match(r"^#[0-9A-Fa-f]{6}$", candidate):
            raise serializers.ValidationError(_("Color must be a HEX value like #3f51b5."))
        return candidate

    def validate_course_ids(self, courses):
        request = self.context.get("request")
        user = request.user if request else None
        if not user:
            return courses
        if user.role == User.Role.COURSE_ADMIN:
            for course in courses:
                if not course.admins.filter(id=user.id).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )
        elif user.role == User.Role.MANAGER:
            for course in courses:
                if user.company and not course.admins.filter(company=user.company).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )
        return courses

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        teacher = super().update(instance, validated_data)
        if password:
            teacher.set_password(password)
            teacher.save(update_fields=["password"])
        return teacher

class CourseAdminUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
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

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def validate_max_pages(self, value):
        if value < 1:
            raise serializers.ValidationError(_("Pages limit must be at least 1."))
        return value

    def validate_max_blocks(self, value):
        if value < 1:
            raise serializers.ValidationError(_("Blocks limit must be at least 1."))
        return value

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"), password=attrs.get("password")
        )
        if not user:
            raise serializers.ValidationError(_("Invalid credentials."))
        attrs["user"] = user
        return attrs

class StudentIdentityLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=False
    )

class StudentSetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return attrs

class StudentProfileSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=False)
    telegram = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(
        required=False, allow_blank=True, write_only=True, trim_whitespace=False, min_length=6
    )

from .domains.courses.serializers import CourseSerializer


class AuditoriumSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Auditorium
        fields = ("id", "name", "number", "company", "company_id", "created_at")
        read_only_fields = ()

from .domains.students.serializers import (
    StudentSerializer,
    TransferGroupSerializer,
)


class GroupSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    student_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Student.objects.all(), required=False
    )
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_price = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    teacher_color = serializers.SerializerMethodField()
    lesson_duration_minutes = serializers.IntegerField(
        source="course.lesson_duration_minutes", read_only=True
    )
    auditorium_label = serializers.SerializerMethodField()
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "course",
            "course_title",
            "course_price",
            "teacher",
            "teacher_name",
            "teacher_color",
            "students",
            "student_ids",
            "status",
            "is_login_allowed",
            "schedule_days",
            "schedule_time",
            "lesson_duration_minutes",
            "auditorium",
            "auditorium_label",
            "lessons_count",
            "lessons_per_month",
            "total_months",
            "start_date",
            "end_date",
            "created_at",
            "company",
            "company_id",
            "teacher_percent",
        )
        read_only_fields = ("status",)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if request.user.role == User.Role.STUDENT:
                fields.pop("students", None)
        return fields

    def create(self, validated_data):
        student_ids = validated_data.pop("student_ids", [])
        group = super().create(validated_data)
        if student_ids:
            group.students.set(student_ids)
        return group

    def update(self, instance, validated_data):
        student_ids = validated_data.pop("student_ids", None)
        group = super().update(instance, validated_data)
        if student_ids is not None:
            group.students.set(student_ids)
        return group

    def get_teacher_name(self, obj):
        teacher = getattr(obj, 'teacher', None)
        if teacher:
            return f"{teacher.first_name} {teacher.last_name}".strip() or str(teacher)
        return ""

    def get_teacher_color(self, obj):
        if not obj.teacher:
            return ""
        return obj.teacher.color or "#45B2EF"

    def get_auditorium_label(self, obj):
        if obj.auditorium:
            return str(obj.auditorium)
        return None

    def get_course_price(self, obj):
        if obj.course and hasattr(obj.course, 'price'):
            return float(obj.course.price)
        return 0.0

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ("id", "group", "student", "date", "status", "created_at")

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = (
            "id", "company", "description", "amount", "category", "date",
            "created_at", "updated_at",
        )
        read_only_fields = ("company",)

class GroupMonthSerializer(serializers.ModelSerializer):
    teacher_percent_earning = serializers.SerializerMethodField()
    teacher_total_earning = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    month_label = serializers.SerializerMethodField()

    class Meta:
        model = GroupMonth
        fields = (
            "id", "group", "group_name", "month_number", "month_label", "teacher_salary", "status",
            "completed_at", "created_at",
            "teacher_percent_earning", "teacher_total_earning",
            "teacher_name",
        )
        read_only_fields = ("created_at",)

    def get_month_label(self, obj):
        """Вычисляем реальный месяц/год на основе start_date группы и month_number."""
        group = obj.group
        start_date = getattr(group, "start_date", None)
        if not start_date:
            return f"Месяц {obj.month_number}"
        # month_number=1 → start_date, month_number=2 → start_date + 1 месяц и т.д.
        from dateutil.relativedelta import relativedelta
        month_date = start_date + relativedelta(months=obj.month_number - 1)
        months_russian = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return f"{months_russian[month_date.month - 1]} {month_date.year}"

    def get_teacher_name(self, obj):
        group = obj.group
        if not group:
            return None
        teacher = getattr(group, "teacher", None)
        if teacher:
            return f"{teacher.first_name} {teacher.last_name}".strip() or str(teacher)
        return None

    def get_teacher_percent_earning(self, obj):
        """Вычисляем автоматический % учителя за месяц: students × course_price × teacher_percent / 100"""
        group = obj.group
        teacher_percent = group.teacher_percent or 0
        course = group.course
        if not teacher_percent or teacher_percent <= 0 or not course:
            return 0
        student_count = group.students.count() or 0
        if student_count == 0:
            return 0
        course_price = course.price or 0
        return int((course_price * student_count * teacher_percent) / 100)

    def get_teacher_total_earning(self, obj):
        """Общий заработок учителя за месяц: teacher_salary + teacher_percent_earning"""
        salary = int(obj.teacher_salary) if obj.teacher_salary else 0
        percent = self.get_teacher_percent_earning(obj)
        return salary + percent

class PaymentSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Payment
        fields = ("id", "student", "group", "company", "company_id", "amount", "status", "paid_at", "due_date", "reminder_sent_at", "created_at")

from .domains.homework.serializers import (
    HomeworkSubmissionSerializer,
    HomeworkTaskAttachmentSerializer,
    HomeworkTaskSerializer,
)


from .domains.trials.serializers import TrialLeadSerializer


from .domains.tasks.serializers import TaskSerializer


from .domains.landing.serializers import (
    LandingSectionSerializer,
    LandingHeaderLinkSerializer,
    LandingPageSerializer,
    LandingPublicSectionSerializer,
    LandingPublicPageSerializer,
)


from .domains.contracts.serializers import (
    ContractSerializer,
    ContractTemplateSerializer,
)


class PromoCodeSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = (
            "id",
            "code",
            "reward_type",
            "reward_value",
            "max_usages",
            "current_usages",
            "expiry_date",
            "is_active",
            "balance",
            "created_by",
            "created_at",
        )
        read_only_fields = ("current_usages", "created_by", "created_at", "balance")

    def get_balance(self, obj):
        """Получить баланс промокода"""
        try:
            return obj.balance.balance if hasattr(obj, 'balance') and obj.balance else 0
        except Exception:
            return 0

from .domains.marketplace.serializers import (
    CompanySerializer,
    PublicCourseSerializer,
    JobVacancySerializer,
    JobVacancyDetailSerializer,
    CompanyCreateUpdateSerializer,
)


class TeacherApplicationSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TeacherApplication
        fields = (
            "id", "full_name", "phone", "email", "experience",
            "specialization", "expected_salary", "education", "about",
            "availability", "format", "company", "company_id",
            "status", "created_at", "updated_at",
        )
        read_only_fields = ("status", "created_at", "updated_at")

class StudentApplicationSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = StudentApplication
        fields = (
            "id", "full_name", "phone", "email", "age",
            "course_interest", "experience_level", "learning_goal",
            "budget", "schedule_preference", "source",
            "company", "company_id",
            "status", "created_at", "updated_at",
        )
        read_only_fields = ("status", "created_at", "updated_at")
