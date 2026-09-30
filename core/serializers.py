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


from .domains.users.serializers import (
    UserSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    CourseAdminUpdateSerializer,
    LoginSerializer,
    StudentIdentityLoginSerializer,
    StudentSetPasswordSerializer,
    StudentProfileSerializer,
)


from .domains.courses.serializers import CourseSerializer


from .domains.auditoriums.serializers import AuditoriumSerializer


from .domains.students.serializers import (
    StudentSerializer,
    TransferGroupSerializer,
)


from .domains.groups.serializers import GroupSerializer


from .domains.attendance.serializers import AttendanceSerializer


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

from .domains.payments.serializers import PaymentSerializer


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
