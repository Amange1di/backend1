from dateutil.relativedelta import relativedelta
from rest_framework import serializers

from core.models import Expense, GroupMonth


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = (
            "id",
            "company",
            "description",
            "amount",
            "category",
            "date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("company",)


class GroupMonthSerializer(serializers.ModelSerializer):
    teacher_percent_earning = serializers.SerializerMethodField()
    teacher_total_earning = serializers.SerializerMethodField()
    group_name = serializers.CharField(
        source="group.name",
        read_only=True,
    )
    teacher_name = serializers.SerializerMethodField()
    month_label = serializers.SerializerMethodField()

    class Meta:
        model = GroupMonth
        fields = (
            "id",
            "group",
            "group_name",
            "month_number",
            "month_label",
            "teacher_salary",
            "status",
            "completed_at",
            "created_at",
            "teacher_percent_earning",
            "teacher_total_earning",
            "teacher_name",
        )
        read_only_fields = ("created_at",)

    def get_month_label(self, obj):
        group = obj.group
        start_date = getattr(group, "start_date", None)
        if not start_date:
            return {
                "key": "month_number",
                "month_number": obj.month_number,
                "year": None,
            }

        month_date = start_date + relativedelta(
            months=obj.month_number - 1
        )
        return {
            "key": f"month_{month_date.month:02d}",
            "month_number": month_date.month,
            "year": month_date.year,
        }

    def get_teacher_name(self, obj):
        group = obj.group
        if not group:
            return None

        teacher = getattr(
            group,
            "teacher",
            None,
        )
        if teacher:
            return (
                f"{teacher.first_name} "
                f"{teacher.last_name}"
            ).strip() or str(teacher)
        return None

    def get_teacher_percent_earning(self, obj):
        group = obj.group
        teacher_percent = (
            group.teacher_percent
            or 0
        )
        course = group.course

        if (
            not teacher_percent
            or teacher_percent <= 0
            or not course
        ):
            return 0

        student_count = (
            group.students.count()
            or 0
        )
        if student_count == 0:
            return 0

        course_price = course.price or 0
        return int(
            (
                course_price
                * student_count
                * teacher_percent
            )
            / 100
        )

    def get_teacher_total_earning(self, obj):
        salary = (
            int(obj.teacher_salary)
            if obj.teacher_salary
            else 0
        )
        percent = (
            self.get_teacher_percent_earning(
                obj
            )
        )
        return salary + percent
