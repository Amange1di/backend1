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


class UserBalanceHistoryView(APIView):
    """История транзакций eduCoin для компании"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            return Response(
                {"detail": "Доступно только для course_admin и manager."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        company_name = resolve_user_company_name(request.user)
        if not company_name:
            return Response(
                {"detail": "Компания не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Находим компанию пользователя (учитывая created_by для менеджеров)
        user_company = request.user.company
        if not user_company and request.user.role == User.Role.MANAGER:
            company_name = resolve_user_company_name(request.user)
            if company_name:
                user_company = Company.objects.filter(name=company_name).first()
        if not user_company:
            return Response(
                {"detail": "Компания не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        transactions = Transaction.objects.filter(
            company=user_company
        ).order_by("-timestamp")
        
        # Получаем баланс компании
        balance = 0
        try:
            company_balance = CompanyBalance.objects.get(company=user_company)
            balance = company_balance.balance
        except CompanyBalance.DoesNotExist:
            pass
        
        data = []
        for t in transactions:
            data.append({
                "id": t.id,
                "amount": t.amount,
                "reason": t.reason,
                "transaction_type": t.transaction_type,
                "transaction_type_display": t.get_transaction_type_display(),
                "timestamp": t.timestamp.isoformat(),
                "balance_after": balance,
            })
            balance -= t.amount
        
        return Response({
            "balance": CompanyBalance.objects.filter(company=user_company).first().balance if CompanyBalance.objects.filter(company=user_company).exists() else 0,
            "transactions": data,
        })


class UserBalanceMeView(APIView):
    """Текущий баланс компании eduCoin"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            return Response(
                {"detail": "Доступно только для course_admin и manager."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Находим компанию пользователя (учитывая created_by для менеджеров)
        user_company = request.user.company
        if not user_company and request.user.role == User.Role.MANAGER:
            company_name = resolve_user_company_name(request.user)
            if company_name:
                user_company = Company.objects.filter(name=company_name).first()
        if not user_company:
            return Response(
                {"balance": 0},
            )
        
        balance = 0
        try:
            company_balance = CompanyBalance.objects.get(company=user_company)
            balance = company_balance.balance
        except CompanyBalance.DoesNotExist:
            pass
        
        return Response({
            "balance": balance,
            "company_name": user_company.name,
        })


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


class CrmContactView(APIView):
    """Public endpoint for the CRM's own landing page contact form.

    Creates a TrialLead without company association and notifies superadmins.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, PublicSubmitThrottle]
    parser_classes = [JSONParser]

    def post(self, request):
        full_name = (request.data.get("full_name") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        if not full_name or not phone:
            return Response(
                {"detail": "Full name and phone are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = (request.data.get("comment") or "").strip()
        telegram = (request.data.get("telegram") or "").strip()

        # Санитизация полей от HTML перед сохранением
        safe_full_name = bleach.clean(full_name, tags=[], strip=True)[:200]
        safe_comment = bleach.clean(comment, tags=[], strip=True)[:1000]
        safe_telegram = bleach.clean(telegram, tags=[], strip=True)[:200]

        # Save as TrialLead with source "crm-landing" (no company)
        comment_parts = []
        if safe_comment:
            comment_parts.append(safe_comment)
        if safe_telegram:
            comment_parts.append(f"Telegram: {safe_telegram}")
        lead = TrialLead.objects.create(
            full_name=safe_full_name,
            phone=phone,
            source="crm-landing",
            comment="\n".join(comment_parts),
            company=None,
        )

        # Notify superadmins (используем санитизированные данные)
        try:
            from telegram_bot.notifications import send_crm_contact_notification
            from asgiref.sync import async_to_sync

            async_to_sync(send_crm_contact_notification)(
                full_name=safe_full_name,
                phone=phone,
                comment=safe_comment,
                telegram=safe_telegram,
            )
        except Exception as e:
            logger.warning(f"Failed to send CRM contact notification: {e}")

        return Response(
            {"id": lead.id, "detail": "Contact request received."},
            status=status.HTTP_201_CREATED,
        )


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


class UserBalanceMeView(APIView):
    """
    Get current user's eduCoin balance.
    GET /api/user/balance/me/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_balance, created = UserBalance.objects.get_or_create(user=user)
        return Response({'balance': user_balance.balance})


# Compatibility re-export. New code should import from core.domains.contracts.views.
from .domains.contracts.views import (
    ContractViewSet,
    ContractTemplateViewSet,
    StudentContractsView,
)


class CspReportView(APIView):
    """
    Public endpoint для сбора CSP violation report-ов.
    Браузеры отправляют POST с Content-Type application/csp-report (не application/json!), 
    поэтому читаем тело вручную через json.loads(request.body).
    Все нарушения логируются для мониторинга.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # No auth needed for CSP reports

    def post(self, request):
        import json
        try:
            report = json.loads(request.body)
        except (ValueError, AttributeError, TypeError):
            # Невалидный JSON или пустое тело — игнорируем
            return Response(status=204)
        
        # CSP report может быть в формате {"csp-report": {...}} или плоским
        csp_report = report.get("csp-report", report)
        
        if not isinstance(csp_report, dict):
            return Response(status=204)
        
        blocked_uri = csp_report.get("blocked-uri", "unknown")
        violated_directive = csp_report.get("violated-directive", "unknown")
        document_uri = csp_report.get("document-uri", "unknown")
        original_policy = csp_report.get("original-policy", "")
        disposition = csp_report.get("disposition", "unknown")
        source_file = csp_report.get("source-file", "")
        line_number = csp_report.get("line-number", "")
        
        logger.warning(
            "CSP Violation | directive=%s | blocked=%s | document=%s | disposition=%s | source=%s:%s | policy=%s",
            violated_directive,
            blocked_uri,
            document_uri,
            disposition,
            source_file,
            line_number,
            original_policy[:500],
        )
        
        # В production можно также сохранять в БД, отправлять в Sentry и т.д.
        if settings.DEBUG:
            logger.debug("Full CSP report: %s", csp_report)
        
        return Response(status=204)  # No content — браузеру не нужен ответ

