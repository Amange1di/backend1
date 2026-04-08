from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Attendance,
    Auditorium,
    Course,
    Group,
    Payment,
    Student,
    TrialLead,
    Task,
    User,
)


class UserSerializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    managers_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "company_name",
            "created_by",
            "role",
            "is_active",
            "max_managers",
            "managers_count",
        )

    def get_managers_count(self, obj):
        return obj.get_managers_count() if obj.role == User.Role.COURSE_ADMIN else 0


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

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
            "company_name",
            "max_managers",
            "role",
        )

    def validate_role(self, value):
        if isinstance(value, str):
            return value.lower()
        return value

    def create(self, validated_data):
        forced_role = self.context.get("force_role")
        role = forced_role or validated_data.get("role", User.Role.TEACHER)
        created_by = validated_data.get("created_by")
        user = User(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            telegram=validated_data.get("telegram", ""),
            company_name=validated_data.get("company_name", ""),
            max_managers=validated_data.get("max_managers", 0) or 0,
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


class CourseAdminUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "company_name",
            "is_active",
            "max_managers",
            "password",
        )

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


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


class CourseSerializer(serializers.ModelSerializer):
    admins = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=User.objects.filter(role=User.Role.COURSE_ADMIN),
    )

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "price",
            "duration_weeks",
            "lesson_duration_minutes",
            "description",
            "schedule",
            "admins",
            "created_at",
        )


class AuditoriumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auditorium
        fields = ("id", "name", "number", "company_name", "created_at")
        read_only_fields = ("company_name",)


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.STUDENT),
        required=False,
        allow_null=True,
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Group.objects.all(), required=False
    )
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Student
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "phone",
            "telegram",
            "company_name",
            "primary_course",
            "group_ids",
            "groups",
            "notes",
            "created_at",
        )
        read_only_fields = ("company_name",)

    def create(self, validated_data):
        group_ids = validated_data.pop("group_ids", [])
        student = super().create(validated_data)
        if group_ids:
            student.groups.set(group_ids)
        return student

    def update(self, instance, validated_data):
        group_ids = validated_data.pop("group_ids", None)
        student = super().update(instance, validated_data)
        if group_ids is not None:
            student.groups.set(group_ids)
        return student


class GroupSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    student_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Student.objects.all(), required=False
    )
    course_title = serializers.CharField(source="course.title", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    lesson_duration_minutes = serializers.IntegerField(
        source="course.lesson_duration_minutes", read_only=True
    )
    auditorium_label = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "course",
            "course_title",
            "teacher",
            "teacher_name",
            "students",
            "student_ids",
            "schedule_days",
            "schedule_time",
            "lesson_duration_minutes",
            "auditorium",
            "auditorium_label",
            "lessons_count",
            "start_date",
            "end_date",
            "created_at",
        )

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
        if not obj.teacher:
            return ""
        full_name = f"{obj.teacher.first_name} {obj.teacher.last_name}".strip()
        return full_name or obj.teacher.username

    def get_auditorium_label(self, obj):
        if not obj.auditorium:
            return ""
        name = obj.auditorium.name or ""
        number = obj.auditorium.number or ""
        label = f"{name} {number}".strip()
        return label or name or number


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ("id", "group", "student", "date", "status", "created_at")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "student", "group", "amount", "status", "paid_at", "created_at")


class TrialLeadSerializer(serializers.ModelSerializer):
    group_assigned_label = serializers.CharField(
        source="group_assigned.name", read_only=True
    )

    class Meta:
        model = TrialLead
        fields = (
            "id",
            "full_name",
            "phone",
            "age",
            "course_interest",
            "trial_attended",
            "status",
            "trial_date",
            "source",
            "comment",
            "converted_to_student",
            "group_assigned",
            "group_assigned_label",
            "payment_status",
            "company_name",
            "created_at",
        )
        read_only_fields = ("company_name",)


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)

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
            "company_name",
            "created_at",
        )
        read_only_fields = ("company_name",)

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return ""
        full_name = f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
        return full_name or obj.assigned_to.username
