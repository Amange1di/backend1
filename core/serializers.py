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


from .domains.finance.serializers import (
    ExpenseSerializer,
    GroupMonthSerializer,
)


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


from .domains.promo_codes.serializers import PromoCodeSerializer


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
