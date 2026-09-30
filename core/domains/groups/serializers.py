from rest_framework import serializers

from core.models import Company, Group, Student, User
from core.domains.students.serializers import StudentSerializer


class GroupSerializer(serializers.ModelSerializer):
    students = StudentSerializer(
        many=True,
        read_only=True,
    )
    student_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Student.objects.all(),
        required=False,
    )
    course_title = serializers.CharField(
        source="course.title",
        read_only=True,
    )
    course_price = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    teacher_color = serializers.SerializerMethodField()
    lesson_duration_minutes = serializers.IntegerField(
        source="course.lesson_duration_minutes",
        read_only=True,
    )
    auditorium_label = serializers.SerializerMethodField()
    company_id = serializers.IntegerField(
        read_only=True,
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
        read_only_fields = ("status", "company", "company_id")

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        if (
            request
            and request.user.is_authenticated
            and request.user.role == User.Role.STUDENT
        ):
            fields.pop("students", None)

        return fields

    def create(self, validated_data):
        student_ids = validated_data.pop(
            "student_ids",
            [],
        )
        group = super().create(validated_data)

        if student_ids:
            group.students.set(student_ids)

        return group

    def update(
        self,
        instance,
        validated_data,
    ):
        student_ids = validated_data.pop(
            "student_ids",
            None,
        )
        group = super().update(
            instance,
            validated_data,
        )

        if student_ids is not None:
            group.students.set(student_ids)

        return group

    def get_teacher_name(self, obj):
        teacher = getattr(
            obj,
            "teacher",
            None,
        )
        if teacher:
            return (
                f"{teacher.first_name} "
                f"{teacher.last_name}"
            ).strip() or str(teacher)
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
        if (
            obj.course
            and hasattr(obj.course, "price")
        ):
            return float(obj.course.price)
        return 0.0
