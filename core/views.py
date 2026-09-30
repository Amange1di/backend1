from datetime import date, timedelta
from calendar import monthrange
import re

from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
import io
import os

import logging
import bleach

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
    HomeworkSubmission,
    HomeworkTask,
    Payment,
    Student,
    TrialLead,
    Task,
    TaskLead,
    User,
    TelegramBindCode,
    CompanyBalance,
    PromoCode,
    Transaction,
    Company,
    CompanyCategory,
    CompanyCity,
    PublicCourse,
    JobVacancy,
    StudentApplication,
    UserBalance,
    Contract,
)
from .permissions import (
    IsAdmin,
    IsCourseAdmin,
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
    IsCourseAdminOrManagerOrStudentReadOnly,
    IsCourseAdminOrTeacherReadOnly,
    IsTeacherOrCourseAdminReadOnly,
)

logger = logging.getLogger(__name__)


class LoginThrottle(AnonRateThrottle):
    """Rate limiting для login endpoints"""
    rate = '1000/hour'


class RegisterThrottle(AnonRateThrottle):
    """Rate limiting для registration endpoints"""
    rate = '1000/hour'


class PublicSubmitThrottle(AnonRateThrottle):
    """Rate limiting для публичных форм отправки (landing leads, crm contact)"""
    rate = '10/minute'


class PublicReadThrottle(AnonRateThrottle):
    """Rate limiting для публичных GET endpoints (landing pages)"""
    rate = '60/minute'


from .permissions import (
    IsAdmin,
    IsCourseAdmin,
    IsCourseAdminOrManager,
    IsCourseAdminOrManagerReadOnly,
    IsCourseAdminOrManagerOrStudentReadOnly,
    IsCourseAdminOrTeacherReadOnly,
    IsTeacherOrCourseAdminReadOnly,
)
from .serializers import (
    TrialLeadSerializer,
)


# Compatibility re-export. New code should import from core.domains.auth.
from .domains.auth.views import (
    RegisterView,
    LoginView,
    LogoutView,
    StudentLoginView,
    StudentSetPasswordView,
    StudentProfileView,
    CourseAdminCreateView,
    CourseAdminDetailView,
    MeView,
)
from .domains.auth.services import (
    resolve_support_telegram,
    get_company_student_cabinet_enabled,
    student_has_allowed_group,
    ensure_student_access_allowed,
)
from .domains.users.services import resolve_user_company_name


# Compatibility re-export. New code should import from core.domains.balances.views.
from .domains.balances.views import (
    UserBalanceHistoryView,
    UserBalanceMeView,
)


def resolve_support_telegram(user: User) -> str:
    if user.role == User.Role.COURSE_ADMIN:
        admin = (
            user.created_by
            if user.created_by and user.created_by.role == User.Role.ADMIN
            else None
        )
        if admin and admin.telegram:
            return admin.telegram
        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("date_joined").first()
        )
        return admin.telegram if admin and admin.telegram else ""
    if user.role in (User.Role.TEACHER, User.Role.MANAGER, User.Role.STUDENT):
        if user.created_by and user.created_by.telegram:
            return user.created_by.telegram
        if user.company:
            course_admin = (
                User.objects.filter(
                    role=User.Role.COURSE_ADMIN, company=user.company
                )
                .order_by("date_joined")
                .first()
            )
            return (
                course_admin.telegram if course_admin and course_admin.telegram else ""
            )
        return ""
    if user.role == User.Role.ADMIN:
        return user.telegram or ""
    return ""


def get_company_student_cabinet_enabled(company):
    if not company:
        return False
    return User.objects.filter(
        role=User.Role.COURSE_ADMIN,
        company=company,
        is_student_cabinet_enabled=True,
    ).exists()


def student_has_allowed_group(student: Student) -> bool:
    groups = student.groups.all()
    if not groups.exists():
        return True
    return groups.filter(is_login_allowed=True).exists()


def ensure_student_access_allowed(student: Student):
    if not student.company or not get_company_student_cabinet_enabled(student.company.name if student.company else ""):
        raise PermissionDenied("Student cabinet is disabled for this company.")
    if not student.can_login:
        raise PermissionDenied("Student login is disabled for this account.")
    if not student_has_allowed_group(student):
        raise PermissionDenied("Student login is disabled for this group.")
    if not student.user or student.user.role != User.Role.STUDENT:
        raise PermissionDenied("Student account is not configured.")
    if not student.user.is_active:
        raise PermissionDenied("Student account is inactive.")


# Compatibility re-export. New code should import from core.domains.courses.views.
from .domains.courses.views import CourseViewSet


# Compatibility re-export. New code should import from core.domains.students.views.
from .domains.students.views import StudentViewSet


# Compatibility re-export. New code should import from domain views.
from .domains.teachers.views import TeacherViewSet
from .domains.managers.views import ManagerViewSet


# Compatibility re-export. New code should import from core.domains.groups.views.
from .domains.groups.views import GroupViewSet


# Compatibility re-export. New code should import from domain views.
from .domains.auditoriums.views import AuditoriumViewSet
from .domains.attendance.views import AttendanceViewSet
from .domains.payments.views import PaymentViewSet


# Compatibility re-export. New code should import from core.domains.super_admin.views.
from .domains.super_admin.views import (
    DashboardView,
    SuperAdminStatsView,
)


# Compatibility re-export. New code should import from core.domains.landing.views.
from .domains.landing.views import (
    LandingPageViewSet,
    LandingHeaderLinkViewSet,
    PublicLandingDetailView,
    PublicLandingLeadCreateView,
)


# Compatibility re-export. New code should import from core.domains.public.views.
from .domains.public.views import CrmContactView


# Compatibility re-export. New code should import from core.domains.trials.views.
from .domains.trials.views import TrialLeadViewSet


# Compatibility re-export. New code should import from core.domains.tasks.views.
from .domains.tasks.views import TaskViewSet


# Compatibility re-export. New code should import from core.domains.homework.views.
from .domains.homework.views import (
    HomeworkTaskViewSet,
    HomeworkSubmissionViewSet,
)


# Compatibility re-export. Promo routes remain disabled as before.
from .domains.promo_codes.views import PromoCodeViewSet


from .domains.attendance.views import AttendanceMarkView


# Compatibility re-export. New code should import from core.domains.marketplace.views.
from .domains.marketplace.views import (
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    BoostCourseView,
    BoostJobView,
    UrgentCourseView,
    UrgentJobView,
    PublicCourseViewSet,
    PublicJobViewSet,
)


# Create your views here.


# ═══════════════════════════════════════════════════════════════════════
#  TELEGRAM BIND CODE GENERATION
# ═══════════════════════════════════════════════════════════════════════

import random


# Compatibility re-export. New code should import from core.domains.telegram.views.
from .domains.telegram.views import (
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
    BroadcastView,
)


# Compatibility re-export. New code should import from core.domains.finance.views.
from .domains.finance.views import (
    ExpenseViewSet,
    GroupMonthViewSet,
)


# Compatibility re-export. New code should import from core.domains.marketplace.views.
from .domains.marketplace.views import (
    MarketplaceCompanyViewSet,
    MarketplaceCourseViewSet,
    MarketplaceJobViewSet,
    MyCoursesView,
    MyJobsView,
    BoostCourseView,
    BoostJobView,
    UrgentCourseView,
    UrgentJobView,
    PublicCourseViewSet,
    PublicJobViewSet,
)


# Create your views here.


# ═══════════════════════════════════════════════════════════════════════
#  TELEGRAM BIND CODE GENERATION
# ═══════════════════════════════════════════════════════════════════════

import random


# Compatibility re-export. New code should import from core.domains.finance.views.
from .domains.finance.views import (
    FinanceDashboardView,
    FinanceExportView,
)


# Compatibility re-export. New code should import from core.domains.contracts.views.
from .domains.contracts.views import (
    ContractViewSet,
    ContractTemplateViewSet,
    StudentContractsView,
)


from .domains.public.views import CspReportView
