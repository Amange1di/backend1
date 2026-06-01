import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import (
    Company, Student, User, Group, Course, 
    Payment, CompanyBalance, Transaction,
    TaskLead, Task, Auditorium, HomeworkTask,
    HomeworkSubmission, TrialLead, JobVacancy,
    PublicCourse, ApplicationStatus
)

print('=' * 60)
print('ПОЛНЫЙ ОТЧЕТ ПО БАЗЕ ДАННЫХ')
print('=' * 60)

# Компании
companies = Company.objects.all()
print(f'\n🏢 КОМПАНИИ: {companies.count()}')
for c in companies:
    balance = CompanyBalance.objects.filter(company=c).first()
    bal = balance.balance if balance else 0
    students_count = c.students.count()
    managers_count = c.users.filter(role=User.Role.MANAGER).count()
    print(f'  - {c.name}: {students_count} студентов, {managers_count} менеджеров, баланс: {bal} eC')

# Студенты
students = Student.objects.all()
print(f'\n👨‍🎓 СТУДЕНТЫ: {students.count()}')

# Пользователи
users = User.objects.all()
superadmins = users.filter(role=User.Role.SUPER_ADMIN).count()
admins = users.filter(role=User.Role.ADMIN).count()
course_admins = users.filter(role=User.Role.COURSE_ADMIN).count()
managers = users.filter(role=User.Role.MANAGER).count()
teachers = users.filter(role=User.Role.TEACHER).count()
students_users = users.filter(role=User.Role.STUDENT).count()
print(f'\n👥 ПОЛЬЗОВАТЕЛИ: {users.count()}')
print(f'  - Super Admin: {superadmins}')
print(f'  - Admin: {admins}')
print(f'  - Course Admin: {course_admins}')
print(f'  - Manager: {managers}')
print(f'  - Teacher: {teachers}')
print(f'  - Student: {students_users}')

# Балансы
balances = CompanyBalance.objects.all()
total_balance = sum(b.balance for b in balances)
print(f'\n💰 БАЛАНСЫ: {balances.count()} записей')
print(f'  - Общий баланс: {total_balance} eC')

# Транзакции
transactions = Transaction.objects.all()
print(f'\n📊 ТРАНЗАКЦИИ: {transactions.count()}')

# Группы
groups = Group.objects.all()
print(f'\n📚 ГРУППЫ: {groups.count()}')

# Курсы
courses = Course.objects.all()
print(f'\n📖 КУРСЫ (внутренние): {courses.count()}')

# Публичные курсы
public_courses = PublicCourse.objects.all()
print(f'\n🌐 ПУБЛИЧНЫЕ КУРСЫ: {public_courses.count()}')

# Аудитории
auditoriums = Auditorium.objects.all()
print(f'\n🏛️ АУДИТОРИИ: {auditoriums.count()}')

# Payments
payments = Payment.objects.all()
paid = payments.filter(status=Payment.Status.PAID).count()
debt = payments.filter(status=Payment.Status.DEBT).count()
print(f'\n💵 ПЛАТЕЖИ: {payments.count()}')
print(f'  - Оплачено: {paid}')
print(f'  - Долг: {debt}')

# Task Leads
task_leads = TaskLead.objects.all()
print(f'\n👔 TASK LEADS: {task_leads.count()}')

# Задачи
tasks = Task.objects.all()
pending = tasks.filter(status=Task.Status.PENDING).count()
in_progress = tasks.filter(status=Task.Status.IN_PROGRESS).count()
completed = tasks.filter(status=Task.Status.COMPLETED).count()
print(f'\n📋 ЗАДАЧИ: {tasks.count()}')
print(f'  - Ожидают: {pending}')
print(f'  - В процессе: {in_progress}')
print(f'  - Завершено: {completed}')

# Домашние задания
homework_tasks = HomeworkTask.objects.all()
print(f'\n📝 ДОМАШНИЕ ЗАДАНИЯ: {homework_tasks.count()}')

# Сданные задания
submissions = HomeworkSubmission.objects.all()
reviewed = submissions.filter(status=HomeworkSubmission.Status.REVIEWED).count()
pending_sub = submissions.filter(status=HomeworkSubmission.Status.PENDING).count()
print(f'\n✅ СДАННЫЕ ЗАДАНИЯ: {submissions.count()}')
print(f'  - Проверено: {reviewed}')
print(f'  - Ожидают: {pending_sub}')

# Trial Leads
trial_leads = TrialLead.objects.all()
converted = trial_leads.filter(status=TrialLead.Status.CONVERTED).count()
print(f'\n🎯 TRIAL LEADS: {trial_leads.count()}')
print(f'  - Конвертировано: {converted}')

# Vacancies
vacancies = JobVacancy.objects.all()
print(f'\n💼 ВАКАНСИИ: {vacancies.count()}')

# Teacher Applications
teacher_apps = User.objects.filter(role=User.Role.TEACHER).count()
print(f'\n👨‍🏫 ЗАЯВКИ ПРЕПОДАВАТЕЛЕЙ: {teacher_apps}')

print('\n' + '=' * 60)
print('ОТЧЕТ ЗАВЕРШЕН')
print('=' * 60)
