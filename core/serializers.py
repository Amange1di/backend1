import re

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Attendance,
    Auditorium,
    Course,
    Group,
    LandingHeaderLink,
    LandingPage,
    LandingSection,
    HomeworkTaskAttachment,
    HomeworkSubmission,
    HomeworkTask,
    Payment,
    Student,
    TrialLead,
    Task,
    User,
)


def normalize_phone(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def build_student_username(student: Student) -> str:
    base = normalize_phone(student.phone) or f"student{student.id}"
    company = re.sub(r"[^a-z0-9]+", "", (student.company_name or "").lower())[:24]
    prefix = company or "eduosh"
    return f"{prefix}_student_{base}_{student.id}"


def sync_student_user(student: Student, *, created_by=None):
    user = student.user
    if not user:
        user = User(
            username=build_student_username(student),
            role=User.Role.STUDENT,
            company_name=student.company_name,
            created_by=created_by,
            first_name=student.first_name,
            last_name=student.last_name,
            phone=student.phone,
            telegram=student.telegram,
            must_set_password=True,
        )
        user.set_unusable_password()
        user.save()
        student.user = user
        student.save(update_fields=["user"])
        return student

    changed_fields = []
    if user.first_name != student.first_name:
        user.first_name = student.first_name
        changed_fields.append("first_name")
    if user.last_name != student.last_name:
        user.last_name = student.last_name
        changed_fields.append("last_name")
    if user.phone != student.phone:
        user.phone = student.phone
        changed_fields.append("phone")
    if user.telegram != student.telegram:
        user.telegram = student.telegram
        changed_fields.append("telegram")
    if user.company_name != student.company_name:
        user.company_name = student.company_name
        changed_fields.append("company_name")
    if user.role != User.Role.STUDENT:
        user.role = User.Role.STUDENT
        changed_fields.append("role")
    if changed_fields:
        user.save(update_fields=changed_fields)
    return student


class UserSerializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(source="created_by_id", read_only=True)
    managers_count = serializers.SerializerMethodField(read_only=True)
    course_ids = serializers.SerializerMethodField(read_only=True)
    course_titles = serializers.SerializerMethodField(read_only=True)

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
        return obj.get_managers_count() if obj.role == User.Role.COURSE_ADMIN else 0

    def get_course_ids(self, obj):
        if obj.role != User.Role.TEACHER:
            return []
        return list(obj.teaching_courses.values_list("id", flat=True))

    def get_course_titles(self, obj):
        if obj.role != User.Role.TEACHER:
            return []
        return list(obj.teaching_courses.values_list("title", flat=True))


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
        user = User(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            telegram=validated_data.get("telegram", ""),
            company_name=validated_data.get("company_name", ""),
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
                if not course.admins.filter(company_name=user.company_name).exists():
                    raise serializers.ValidationError(
                        "Not allowed to assign this course."
                    )
        return courses

    def create(self, validated_data):
        courses = validated_data.pop("course_ids", [])
        request = self.context.get("request")
        creator = request.user if request else None
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
            company_name=creator.company_name if creator else "",
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
                if not course.admins.filter(company_name=user.company_name).exists():
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

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "address",
            "telegram",
            "company_name",
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
    first_name = serializers.CharField()
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
            "can_login",
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
        request = self.context.get("request")
        sync_student_user(student, created_by=request.user if request else None)
        return student

    def update(self, instance, validated_data):
        group_ids = validated_data.pop("group_ids", None)
        student = super().update(instance, validated_data)
        if group_ids is not None:
            student.groups.set(group_ids)
        request = self.context.get("request")
        sync_student_user(student, created_by=request.user if request else None)
        return student


class GroupSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    student_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Student.objects.all(), required=False
    )
    course_title = serializers.CharField(source="course.title", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    teacher_color = serializers.SerializerMethodField()
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
            "teacher_color",
            "students",
            "student_ids",
            "is_login_allowed",
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

    def get_teacher_color(self, obj):
        if not obj.teacher:
            return ""
        return obj.teacher.color or "#45B2EF"

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


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    is_late = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkSubmission
        fields = (
            "id",
            "task",
            "student",
            "student_name",
            "answer_text",
            "file",
            "file_url",
            "status",
            "grade",
            "teacher_comment",
            "is_late",
            "submitted_at",
        )
        read_only_fields = ("student", "submitted_at")
        extra_kwargs = {
            "file": {"write_only": True, "required": False, "allow_null": True},
        }

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_student_name(self, obj):
        full_name = f"{obj.student.first_name} {obj.student.last_name}".strip()
        return full_name or str(obj.student.id)

    def validate_grade(self, value):
        if value is None:
            return value
        if value < 0 or value > 100:
            raise serializers.ValidationError(_("Grade must be between 0 and 100."))
        return value

    def get_is_late(self, obj):
        deadline = obj.task.deadline
        if not deadline:
            return False
        grace_delta = timezone.timedelta(minutes=obj.task.grace_period_minutes or 0)
        return obj.submitted_at > (deadline + grace_delta)


class HomeworkTaskAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkTaskAttachment
        fields = ("id", "url", "created_at")

    def get_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class HomeworkTaskSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()
    attachments = HomeworkTaskAttachmentSerializer(many=True, read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    my_submission = serializers.SerializerMethodField()
    submissions = serializers.SerializerMethodField()
    student_status = serializers.SerializerMethodField()
    deadline_state = serializers.SerializerMethodField()
    students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Student.objects.all(),
        required=False,
    )

    class Meta:
        model = HomeworkTask
        fields = (
            "id",
            "group",
            "group_name",
            "teacher",
            "teacher_name",
            "title",
            "description",
            "attachment",
            "attachment_url",
            "attachments",
            "lesson_number",
            "is_extra_task",
            "target_type",
            "students",
            "task_type",
            "deadline",
            "hard_deadline",
            "allow_late",
            "grace_period_minutes",
            "publish_at",
            "is_published",
            "created_at",
            "student_status",
            "deadline_state",
            "my_submission",
            "submissions",
        )
        read_only_fields = ("teacher", "created_at")
        extra_kwargs = {
            "attachment": {"write_only": True, "required": False, "allow_null": True},
        }

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ""
        request = self.context.get("request")
        url = obj.attachment.url
        return request.build_absolute_uri(url) if request else url

    def get_teacher_name(self, obj):
        full_name = f"{obj.teacher.first_name} {obj.teacher.last_name}".strip()
        return full_name or obj.teacher.username

    def get_my_submission(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated or user.role != User.Role.STUDENT:
            return None
        submission = obj.submissions.filter(student__user=user).first()
        if not submission:
            return None
        return HomeworkSubmissionSerializer(submission, context=self.context).data

    def get_submissions(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            return []
        if user.role not in (User.Role.TEACHER, User.Role.COURSE_ADMIN):
            return []
        return HomeworkSubmissionSerializer(
            obj.submissions.select_related("student"),
            many=True,
            context=self.context,
        ).data

    def get_student_status(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated or user.role != User.Role.STUDENT:
            return None
        submission = obj.submissions.filter(student__user=user).first()
        if submission:
            return submission.status
        grace_deadline = obj.deadline + timezone.timedelta(
            minutes=obj.grace_period_minutes or 0
        )
        if timezone.now() > grace_deadline:
            return "missing"
        return "pending"

    def get_deadline_state(self, obj):
        now = timezone.now()
        if obj.deadline <= now:
            return "expired"
        if obj.deadline <= now + timezone.timedelta(hours=24):
            return "warning"
        return "active"

    def validate(self, attrs):
        target_type = attrs.get("target_type") or getattr(
            self.instance, "target_type", HomeworkTask.TargetType.ALL_GROUP
        )
        students = attrs.get("students")
        group = attrs.get("group") or getattr(self.instance, "group", None)
        if target_type == HomeworkTask.TargetType.SPECIFIC_STUDENTS:
            if not students:
                raise serializers.ValidationError(
                    {"students": _("Select at least one student.")}
                )
            if group:
                invalid_students = [student.id for student in students if not group.students.filter(id=student.id).exists()]
                if invalid_students:
                    raise serializers.ValidationError(
                        {"students": _("Selected students must belong to the group.")}
                    )
        return attrs


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


class LandingSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingSection
        fields = (
            "id",
            "section_type",
            "order",
            "content",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class LandingHeaderLinkSerializer(serializers.ModelSerializer):
    target_page_slug = serializers.CharField(source="target_page.slug", read_only=True)
    target_page_title = serializers.CharField(source="target_page.title", read_only=True)

    class Meta:
        model = LandingHeaderLink
        fields = (
            "id",
            "label",
            "target_page",
            "target_page_slug",
            "target_page_title",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_target_page(self, value):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.role == User.Role.COURSE_ADMIN and value.company_name != user.company_name:
            raise serializers.ValidationError(_("You can only link to your own landing pages."))
        return value


class LandingPageSerializer(serializers.ModelSerializer):
    sections = LandingSectionSerializer(many=True, required=False)
    header_links = serializers.SerializerMethodField()
    owner = serializers.IntegerField(source="owner_id", read_only=True)
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "company_name",
            "owner",
            "status",
            "moderation_comment",
            "submitted_at",
            "moderated_at",
            "published_at",
            "created_at",
            "updated_at",
            "sections_count",
            "sections",
            "header_links",
        )
        read_only_fields = (
            "company_name",
            "owner",
            "status",
            "moderation_comment",
            "submitted_at",
            "moderated_at",
            "published_at",
            "created_at",
            "updated_at",
            "sections_count",
            "header_links",
        )

    def get_sections_count(self, obj):
        return obj.sections.count()

    def get_header_links(self, obj):
        links = LandingHeaderLink.objects.filter(company_name=obj.company_name).select_related(
            "target_page"
        )
        return LandingHeaderLinkSerializer(links, many=True, context=self.context).data

    def validate_slug(self, value):
        candidate = (value or "").strip().lower()
        if not candidate:
            raise serializers.ValidationError(_("Slug is required."))
        return candidate

    def validate_sections(self, value):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.role == User.Role.COURSE_ADMIN and len(value) > user.max_blocks:
            raise serializers.ValidationError(
                _("This admin cannot add more than %(limit)s blocks to one page.")
                % {"limit": user.max_blocks}
            )
        return value

    def _sync_sections(self, page: LandingPage, sections_data):
        if sections_data is None:
            return
        page.sections.all().delete()
        LandingSection.objects.bulk_create(
            [
                LandingSection(
                    page=page,
                    section_type=section["section_type"],
                    order=section.get("order", index),
                    content=section.get("content", {}),
                )
                for index, section in enumerate(sections_data)
            ]
        )

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        page = super().create(validated_data)
        self._sync_sections(page, sections_data)
        return page

    def update(self, instance, validated_data):
        sections_data = validated_data.pop("sections", None)
        page = super().update(instance, validated_data)
        self._sync_sections(page, sections_data)
        return page


class LandingPublicSectionSerializer(serializers.ModelSerializer):
    resolved_content = serializers.SerializerMethodField()

    class Meta:
        model = LandingSection
        fields = (
            "id",
            "section_type",
            "order",
            "content",
            "resolved_content",
        )

    def get_resolved_content(self, obj):
        content = dict(obj.content or {})
        company_name = obj.page.company_name
        if obj.section_type == LandingSection.SectionType.COURSE_GRID:
            content["courses"] = list(
                Course.objects.filter(admins__company_name=company_name)
                .distinct()
                .values(
                    "id",
                    "title",
                    "price",
                    "duration_weeks",
                    "lesson_duration_minutes",
                    "description",
                )
            )
        elif obj.section_type == LandingSection.SectionType.TEACHER_SLIDER:
            content["teachers"] = list(
                User.objects.filter(role=User.Role.TEACHER, company_name=company_name)
                .order_by("first_name", "last_name")
                .values(
                    "id",
                    "first_name",
                    "last_name",
                    "phone",
                    "telegram",
                    "working_hours",
                    "color",
                )
            )
        return content


class LandingPublicPageSerializer(serializers.ModelSerializer):
    sections = LandingPublicSectionSerializer(many=True, read_only=True)
    header_links = serializers.SerializerMethodField()

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "company_name",
            "status",
            "published_at",
            "sections",
            "header_links",
        )

    def get_header_links(self, obj):
        links = LandingHeaderLink.objects.filter(
            company_name=obj.company_name,
            target_page__status=LandingPage.Status.ACTIVE,
        ).select_related("target_page")
        return LandingHeaderLinkSerializer(links, many=True, context=self.context).data
