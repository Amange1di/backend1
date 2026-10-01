from django.db import models
from django.db.models import Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Auditorium,
    Company,
    CompanyBalance,
    Course,
    Group,
    HomeworkSubmission,
    HomeworkTask,
    JobVacancy,
    Payment,
    PublicCourse,
    Student,
    Task,
    TaskLead,
    Transaction,
    TrialLead,
    User,
)
from core.permissions import IsAdmin


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
