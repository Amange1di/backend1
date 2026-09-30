from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import (
    Company,
    HomeworkSubmission,
    HomeworkTask,
    HomeworkTaskAttachment,
    Student,
    User,
)


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
            "file": {
                "write_only": True,
                "required": False,
                "allow_null": True,
            },
        }

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_student_name(self, obj):
        full_name = (
            f"{obj.student.first_name} {obj.student.last_name}".strip()
        )
        return full_name or str(obj.student.id)

    def validate_grade(self, value):
        if value is None:
            return value
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                _("Grade must be between 0 and 100.")
            )
        return value

    def get_is_late(self, obj):
        deadline = obj.task.deadline
        if not deadline:
            return False
        grace_delta = timezone.timedelta(
            minutes=obj.task.grace_period_minutes or 0
        )
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
    attachments = HomeworkTaskAttachmentSerializer(
        many=True,
        read_only=True,
    )
    group_name = serializers.CharField(
        source="group.name",
        read_only=True,
    )
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
    company_id = serializers.PrimaryKeyRelatedField(
        source="company",
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
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
            "company",
            "company_id",
        )
        read_only_fields = ("teacher", "created_at")
        extra_kwargs = {
            "attachment": {
                "write_only": True,
                "required": False,
                "allow_null": True,
            },
        }

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ""
        request = self.context.get("request")
        url = obj.attachment.url
        return request.build_absolute_uri(url) if request else url

    def get_teacher_name(self, obj):
        full_name = (
            f"{obj.teacher.first_name} {obj.teacher.last_name}".strip()
        )
        return full_name or obj.teacher.username

    def get_my_submission(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if (
            not user
            or not user.is_authenticated
            or user.role != User.Role.STUDENT
        ):
            return None

        submission = obj.submissions.filter(student__user=user).first()
        if not submission:
            return None

        return HomeworkSubmissionSerializer(
            submission,
            context=self.context,
        ).data

    def get_submissions(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            return []
        if user.role not in (
            User.Role.TEACHER,
            User.Role.COURSE_ADMIN,
        ):
            return []

        return HomeworkSubmissionSerializer(
            obj.submissions.select_related("student"),
            many=True,
            context=self.context,
        ).data

    def get_student_status(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if (
            not user
            or not user.is_authenticated
            or user.role != User.Role.STUDENT
        ):
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
            self.instance,
            "target_type",
            HomeworkTask.TargetType.ALL_GROUP,
        )
        students = attrs.get("students")
        group = attrs.get("group") or getattr(
            self.instance,
            "group",
            None,
        )

        if target_type == HomeworkTask.TargetType.SPECIFIC_STUDENTS:
            if not students:
                raise serializers.ValidationError(
                    {"students": _("Select at least one student.")}
                )

            if group:
                invalid_students = [
                    student.id
                    for student in students
                    if not group.students.filter(
                        id=student.id
                    ).exists()
                ]
                if invalid_students:
                    raise serializers.ValidationError(
                        {
                            "students": _(
                                "Selected students must belong to the group."
                            )
                        }
                    )

        return attrs
