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


class DashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_students = Student.objects.count()
        total_income = (
            Payment.objects.filter(status=Payment.Status.PAID).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        total_debt = (
            Payment.objects.filter(status=Payment.Status.DEBT).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        return Response(
            {
                "total_students": total_students,
                "total_income": total_income,
                "total_debt": total_debt,
            }
        )


class SuperAdminStatsView(APIView):
    """Полная статистика для супер-админа"""
    permission_classes = [IsAdmin]

    def get(self, request):
        # Фильтры
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        company_id = request.query_params.get('company_id')
        search = request.query_params.get('search', '').strip()
        
        # Основная статистика
        companies = Company.objects.all()
        
        # Фильтр компаний
        if company_id:
            companies = companies.filter(id=company_id)
        if search:
            companies = companies.filter(name__icontains=search)
        
        companies_count = companies.count()
        
        students = Student.objects.all()
        students_count = students.count()
        
        users = User.objects.all()
        superadmins = users.filter(role=User.Role.SUPER_ADMIN).count()
        admins = users.filter(role=User.Role.ADMIN).count()
        course_admins = users.filter(role=User.Role.COURSE_ADMIN).count()
        managers = users.filter(role=User.Role.MANAGER).count()
        teachers = users.filter(role=User.Role.TEACHER).count()
        students_users = users.filter(role=User.Role.STUDENT).count()
        
        # Балансы
        balances = CompanyBalance.objects.all()
        total_balance = sum(b.balance for b in balances)
        
        # Средний баланс
        avg_balance = total_balance / companies.count() if companies.count() > 0 else 0
        
        # Транзакции
        transactions_count = Transaction.objects.count()
        
        # Группы
        groups_count = Group.objects.count()
        
        # Курсы
        courses_count = Course.objects.count()
        
        # Публичные курсы
        public_courses_count = PublicCourse.objects.all()
        if date_from or date_to:
            from django.utils import timezone
            from datetime import datetime
            if date_from:
                public_courses_count = public_courses_count.filter(created_at__gte=date_from)
            if date_to:
                public_courses_count = public_courses_count.filter(created_at__lte=date_to)
        public_courses_count = public_courses_count.count()
        
        # Аудитории
        auditoriums_count = Auditorium.objects.count()
        
        # Платежи с фильтрами по дате
        payments = Payment.objects.all()
        if date_from:
            payments = payments.filter(paid_at__gte=date_from)
        if date_to:
            payments = payments.filter(paid_at__lte=date_to)
        payments_count = payments.count()
        paid_count = payments.filter(status=Payment.Status.PAID).count()
        debt_count = payments.filter(status=Payment.Status.DEBT).count()
        total_paid = payments.filter(status=Payment.Status.PAID).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Task Leads
        task_leads_count = TaskLead.objects.count()
        
        # Задачи с фильтрами
        tasks = Task.objects.all()
        if date_from:
            tasks = tasks.filter(created_at__gte=date_from)
        if date_to:
            tasks = tasks.filter(created_at__lte=date_to)
        tasks_count = tasks.count()
        pending_tasks = tasks.filter(status=Task.Status.PENDING).count()
        in_progress_tasks = tasks.filter(status=Task.Status.IN_PROGRESS).count()
        completed_tasks = tasks.filter(status=Task.Status.COMPLETED).count()
        
        # Домашние задания
        homework_tasks_count = HomeworkTask.objects.count()
        
        # Сданные задания
        submissions = HomeworkSubmission.objects.all()
        submissions_count = submissions.count()
        reviewed_submissions = submissions.filter(status=HomeworkSubmission.Status.REVIEWED).count()
        pending_submissions = submissions.filter(status=HomeworkSubmission.Status.PENDING).count()
        
        # Trial Leads
        trial_leads = TrialLead.objects.all()
        if date_from:
            trial_leads = trial_leads.filter(created_at__gte=date_from)
        if date_to:
            trial_leads = trial_leads.filter(created_at__lte=date_to)
        trial_leads_count = trial_leads.count()
        converted_trial_leads = trial_leads.filter(status=TrialLead.Status.CONVERTED).count()
        
        # Конверсия пробных уроков
        conversion_rate = (converted_trial_leads / trial_leads_count * 100) if trial_leads_count > 0 else 0
        
        # Вакансии
        vacancies_count = JobVacancy.objects.all().count()
        
        # Новые регистрации за сегодня
        today = timezone.now().date()
        new_students_today = Student.objects.filter(created_at__date=today).count()
        new_companies_today = Company.objects.filter(created_at__date=today).count()
        new_users_today = User.objects.filter(date_joined__date=today).count()
        
        # Компании без баланса
        companies_no_balance = companies.filter(id__in=CompanyBalance.objects.values('company').annotate(count=models.Count('id')).filter(count=0).values('company')).count()
        
        # Детализация по компаниям
        companies_data = []
        for company in companies:
            balance = CompanyBalance.objects.filter(company=company).first()
            bal = balance.balance if balance else 0
            students_count_company = company.students.count()
            managers_count_company = company.users.filter(role=User.Role.MANAGER).count()
            course_admins_company = company.users.filter(role=User.Role.COURSE_ADMIN).count()
            teachers_count_company = company.users.filter(role=User.Role.TEACHER).count()
            groups_count_company = company.groups.count()
            is_active = company.is_active
            
            companies_data.append({
                "id": company.id,
                "name": company.name,
                "slug": company.slug,
                "city": company.city,
                "category": company.category,
                "students_count": students_count_company,
                "managers_count": managers_count_company,
                "course_admins_count": course_admins_company,
                "teachers_count": teachers_count_company,
                "groups_count": groups_count_company,
                "balance": bal,
                "is_active": is_active,
                "created_at": company.created_at.isoformat(),
            })
        
        # Данные для графиков (динамика по месяцам)
        from django.db.models import Count, Q
        from django.db.models.functions import TruncMonth
        
        # Студенты по месяцам
        monthly_students = Student.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        monthly_students_data = [{'month': m['month'].isoformat(), 'count': m['count']} for m in monthly_students[:12]]
        
        # Платежи по месяцам
        monthly_payments = Payment.objects.filter(status=Payment.Status.PAID).annotate(
            month=TruncMonth('paid_at')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        monthly_payments_data = [{'month': m['month'].isoformat(), 'total': m['total'] or 0, 'count': m['count']} for m in monthly_payments[:12]]
        
        return Response({
            # Основная статистика
            "total_companies": companies_count,
            "total_students": students_count,
            "total_users": users.count(),
            "total_balance": total_balance,
            "avg_balance": round(avg_balance, 2),
            
            # Пользователи по ролям
            "superadmins": superadmins,
            "admins": admins,
            "course_admins": course_admins,
            "managers": managers,
            "teachers": teachers,
            "students_users": students_users,
            
            # Новые регистрации за сегодня
            "new_students_today": new_students_today,
            "new_companies_today": new_companies_today,
            "new_users_today": new_users_today,
            
            # Другие данные
            "transactions": transactions_count,
            "groups": groups_count,
            "courses": courses_count,
            "public_courses": public_courses_count,
            "auditoriums": auditoriums_count,
            
            # Платежи
            "payments_total": payments_count,
            "payments_paid": paid_count,
            "payments_debt": debt_count,
            "total_paid": total_paid,
            
            # Задачи
            "task_leads": task_leads_count,
            "tasks_total": tasks_count,
            "tasks_pending": pending_tasks,
            "tasks_in_progress": in_progress_tasks,
            "tasks_completed": completed_tasks,
            
            # Домашние задания
            "homework_tasks": homework_tasks_count,
            "submissions_total": submissions_count,
            "submissions_reviewed": reviewed_submissions,
            "submissions_pending": pending_submissions,
            
            # Trial Leads
            "trial_leads_total": trial_leads_count,
            "trial_leads_converted": converted_trial_leads,
            "conversion_rate": round(conversion_rate, 2),
            
            # Вакансии
            "vacancies": vacancies_count,
            
            # Статус компаний
            "companies_no_balance": companies_no_balance,
            
            # Детализация по компаниям
            "companies": companies_data,
            
            # Графики
            "charts": {
                "monthly_students": monthly_students_data,
                "monthly_payments": monthly_payments_data,
            }
        })


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


class GenerateTelegramBindCodeView(APIView):
    """
    Generate a one-time code for binding a Telegram account.

    POST /api/bot/generate-bind-code/
    Authenticated user generates a 6-digit code.
    The code is valid for 10 minutes.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Invalidate any existing pending codes for this user
        TelegramBindCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).update(is_used=True)

        # Generate a 6-digit code
        code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=10)

        bind_code = TelegramBindCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at,
            is_used=False,
        )

        return Response({
            "code": bind_code.code,
            "expires_at": bind_code.expires_at.isoformat(),
            "message": (
                f"Код действителен 10 минут. "
                f"Используйте в Telegram: /start {user.username} {bind_code.code}"
            ),
        })


class GetTelegramBindCodeView(APIView):
    """
    Get the current active pending bind code for the authenticated user.

    GET /api/bot/bind-code/
    Returns the code if one exists and is still valid.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        pending_code = TelegramBindCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not pending_code:
            return Response({
                "code": None,
                "message": "Нет активного кода. Сгенерируйте новый.",
            })

        return Response({
            "code": pending_code.code,
            "expires_at": pending_code.expires_at.isoformat(),
        })


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


class GenerateTelegramBindCodeView(APIView):
    """
    Generate a one-time code for binding a Telegram account.

    POST /api/bot/generate-bind-code/
    Authenticated user generates a 6-digit code.
    The code is valid for 10 minutes.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Invalidate any existing pending codes for this user
        TelegramBindCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).update(is_used=True)

        # Generate a 6-digit code
        code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=10)

        bind_code = TelegramBindCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at,
            is_used=False,
        )

        return Response({
            "code": bind_code.code,
            "expires_at": bind_code.expires_at.isoformat(),
            "message": (
                f"Код действителен 10 минут. "
                f"Используйте в Telegram: /start {user.username} {bind_code.code}"
            ),
        })


class GetTelegramBindCodeView(APIView):
    """
    Get the current active pending bind code for the authenticated user.

    GET /api/bot/bind-code/
    Returns the code if one exists and is still valid.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        pending_code = TelegramBindCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).first()

        if not pending_code:
            return Response({
                "code": None,
                "message": "Нет активного кода. Сгенерируйте новый.",
            })

        return Response({
            "code": pending_code.code,
            "expires_at": pending_code.expires_at.isoformat(),
        })


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.none()
    """
    CRUD для расходов компании.
    """
    permission_classes = [IsCourseAdminOrManager]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.COURSE_ADMIN:
            if user.company:
                return Expense.objects.filter(company=user.company)
            return Expense.objects.none()
        if user.role == User.Role.MANAGER:
            if user.company:
                return Expense.objects.filter(company=user.company)
            return Expense.objects.none()
        return Expense.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        company = user.company
        if not company:
            raise PermissionDenied("У вас нет компании для создания расходов.")
        serializer.save(company=company)



class GroupMonthViewSet(viewsets.ModelViewSet):
    queryset = GroupMonth.objects.none()
    """
    CRUD для месяцев обучения группы.
    """
    permission_classes = [IsCourseAdminOrManagerReadOnly]
    serializer_class = GroupMonthSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.Role.COURSE_ADMIN, User.Role.MANAGER):
            if user.company:
                qs = GroupMonth.objects.filter(group__company=user.company)
            else:
                return GroupMonth.objects.none()
        elif user.role == User.Role.TEACHER:
            qs = GroupMonth.objects.filter(group__teacher=user)
        else:
            return GroupMonth.objects.none()
        # Фильтр по группе, если передан параметр ?group=ID
        group_id = self.request.query_params.get("group")
        if group_id and group_id.isdigit():
            qs = qs.filter(group_id=int(group_id))
        # Фильтр по учителю, если передан параметр ?teacher_id=ID
        teacher_id = self.request.query_params.get("teacher_id")
        if teacher_id and teacher_id.isdigit():
            qs = qs.filter(group__teacher_id=int(teacher_id))
        # Фильтр по месяцу, если передан параметр ?month_number=N
        month_number = self.request.query_params.get("month_number")
        if month_number and month_number.isdigit():
            qs = qs.filter(month_number=int(month_number))
        # Фильтр по статусу, если передан параметр ?status=pending|completed
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.select_related("group", "group__course").prefetch_related("group__students")

    def list(self, request, *args, **kwargs):
        # Auto-create все месяцы для группы, если их нет
        group_id = request.query_params.get("group")
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                if group.total_months and group.total_months > 0:
                    existing = set(GroupMonth.objects.filter(
                        group=group
                    ).values_list("month_number", flat=True))
                    for month_number in range(1, group.total_months + 1):
                        if month_number not in existing:
                            GroupMonth.objects.create(
                                group=group,
                                month_number=month_number,
                                status=GroupMonth.Status.PENDING,
                            )
            except Group.DoesNotExist:
                pass
        return super().list(request, *args, **kwargs)

    def _sync_expense_for_month(self, instance: GroupMonth):
        """
        При завершении месяца с зарплатой — создаёт/обновляет расход (Expense).
        При возврате в ожидание — удаляет расход.
        """
        group = instance.group
        if not group.company:
            return
        desc = f"Зарплата: {group.name} — месяц {instance.month_number}"
        if instance.status == GroupMonth.Status.COMPLETED and instance.teacher_salary:
            Expense.objects.update_or_create(
                company=group.company,
                description=desc,
                defaults={
                    "amount": instance.teacher_salary,
                    "category": "salary",
                    "date": instance.completed_at.date() if instance.completed_at else timezone.localdate(),
                },
            )
        elif instance.status == GroupMonth.Status.PENDING:
            Expense.objects.filter(
                company=group.company,
                description=desc,
            ).delete()

    def perform_update(self, serializer):
        """
        При закрытии месяца (completed_at установлен) —
        авто-создаём следующий месяц, если не превышен лимит total_months.
        """
        instance = serializer.save()

        # Проверяем, был ли месяц только что закрыт
        if instance.status == GroupMonth.Status.COMPLETED and instance.completed_at:
            group = instance.group
            next_month_number = instance.month_number + 1

            # Не создаём, если превышает total_months группы
            if not group.total_months or next_month_number > group.total_months:
                return

            # Создаём следующий месяц, если его ещё нет
            GroupMonth.objects.get_or_create(
                group=group,
                month_number=next_month_number,
                defaults={"status": GroupMonth.Status.PENDING},
            )

            # Автоматическое начисление % учителю при завершении месяца
            self._credit_teacher_percent_on_month_completion(instance)

    def _credit_teacher_percent_on_month_completion(self, instance: GroupMonth):
        """
        При завершении месяца начисляет учителю % от стоимости группы.
        Формула: students_count × course_price × teacher_percent / 100.
        Начисляется один раз за каждый завершённый месяц.
        """
        group = instance.group
        teacher = group.teacher
        teacher_percent = group.teacher_percent or 0
        course = group.course

        if not teacher or not course or not teacher_percent or teacher_percent <= 0:
            return

        student_count = group.students.count() or 0
        if student_count == 0:
            return

        try:
            teacher_user = User.objects.get(id=teacher.id)
            course_price = course.price or 0
            total_amount = course_price * student_count
            percent_amount = int((total_amount * teacher_percent) / 100)

            if percent_amount <= 0:
                return

            # Проверяем, не начислялось ли уже за этот месяц
            # Используем Q-объекты для OR-логики поиска по нескольким условиям
            from django.db.models import Q
            already_credited = UserTransaction.objects.filter(
                user=teacher_user,
                amount__gt=0,
                reason__contains=f"месяц {instance.month_number}",
            ).filter(
                Q(reason__contains=group.name) | Q(reason__contains=str(instance.month_number))
            ).exists()

            if already_credited:
                logger.info(
                    f"Teacher {teacher_user.username} already credited for month {instance.month_number} of group {group.name}"
                )
                return

            teacher_balance, created = UserBalance.objects.get_or_create(user=teacher_user)
            reason = (
                f"Начисление %{teacher_percent}% за месяц {instance.month_number} группы «{group.name}» "
                f"({student_count} студ. × {course_price} eC)"
            )
            teacher_balance.add_coins(percent_amount, reason)
            logger.info(
                f"Teacher {teacher_user.username} credited {percent_amount} eC "
                f"for month {instance.month_number} of group {group.name} "
                f"({teacher_percent}% of {student_count} students × {course_price} eC)"
            )
        except Exception as e:
            logger.warning(f"Failed to credit teacher percent on month completion for group {group.id}: {e}")


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


class BroadcastView(APIView):
    """
    Массовая рассылка сообщений через Telegram.
    POST /api/broadcast/send/
    """
    permission_classes = [IsCourseAdminOrManager]

    def post(self, request):
        user = request.user
        company = user.company
        if not company:
            return Response({"detail": "Компания не найдена."}, status=400)

        text = (request.data.get("text") or "").strip()
        target = (request.data.get("target") or "").strip()
        group_id = request.data.get("group_id")

        if not text:
            return Response({"detail": "Текст сообщения обязателен."}, status=400)

        # Санитизация текста через bleach — разрешены только теги Telegram
        text = bleach.clean(
            text,
            tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'],
            attributes={'a': ['href']},
            protocols=['http', 'https', 'mailto'],
            strip=True,
        )

        if len(text) > 4000:
            return Response({"detail": "Текст сообщения не может превышать 4000 символов."}, status=400)

        # Determine recipients
        recipients = []

        if target == "students":
            students = Student.objects.filter(company=company, user__isnull=False)
            for student in students:
                if student.user and student.user.telegram_chat_id:
                    recipients.append({
                        "name": str(student),
                        "chat_id": student.user.telegram_chat_id,
                    })

        elif target == "teachers":
            teachers = User.objects.filter(company=company, role=User.Role.TEACHER)
            for teacher in teachers:
                if teacher.telegram_chat_id:
                    recipients.append({
                        "name": teacher.get_full_name() or teacher.username,
                        "chat_id": teacher.telegram_chat_id,
                    })

        elif target == "managers":
            managers = User.objects.filter(company=company, role=User.Role.MANAGER)
            for mgr in managers:
                if mgr.telegram_chat_id:
                    recipients.append({
                        "name": mgr.get_full_name() or mgr.username,
                        "chat_id": mgr.telegram_chat_id,
                    })

        elif target == "group" and group_id:
            try:
                group = Group.objects.get(id=group_id, company=company)
            except Group.DoesNotExist:
                return Response({"detail": "Группа не найдена."}, status=404)
            for student in group.students.filter(user__isnull=False):
                if student.user and student.user.telegram_chat_id:
                    recipients.append({
                        "name": str(student),
                        "chat_id": student.user.telegram_chat_id,
                    })
        else:
            return Response({"detail": f"Неверный target: {target}"}, status=400)

        if not recipients:
            return Response({"detail": "Нет получателей с привязанным Telegram."}, status=400)

        # Send messages via Telegram
        from telegram_bot.config import _get_application, BOT_TOKEN

        sent_count = 0
        failed_count = 0
        errors = []

        async def send_messages():
            nonlocal sent_count, failed_count
            if not BOT_TOKEN:
                raise Exception("TELEGRAM_BOT_TOKEN не настроен")

            application = _get_application()
            preview_emoji = "📢"
            full_text = f"{preview_emoji} <b>Массовая рассылка</b>\n\n{text}"

            for recipient in recipients:
                try:
                    await application.bot.send_message(
                        chat_id=recipient["chat_id"],
                        text=full_text,
                        parse_mode="HTML",
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{recipient['name']}: {str(e)[:100]}")
                    logger.warning(f"Broadcast failed for {recipient['name']}: {e}")

        try:
            from asgiref.sync import async_to_sync
            async_to_sync(send_messages)()
        except Exception as e:
            return Response({"detail": f"Ошибка отправки: {str(e)}"}, status=500)

        return Response({
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients),
            "errors": errors[:10],
        })


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

