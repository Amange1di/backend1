import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company, Student, Group, Task, TrialLead, Auditorium, LandingPage, HomeworkTask, CompanyBalance

print("=" * 80)
print("ИСПРАВЛЕНИЕ СВЯЗЕЙ КОМПАНИЙ")
print("=" * 80)

# Получаем всех course_admin
course_admins = User.objects.filter(role=User.Role.COURSE_ADMIN)
print(f"\nНайдено Course Admins: {course_admins.count()}")

# Получаем все компании
companies = Company.objects.all()
print(f"Найдено компаний в таблице Company: {companies.count()}")

updated_users = 0
updated_companies = 0

# Связываем course_admin с компаниями
for admin in course_admins:
    admin_company_name = admin.company_name
    
    # Ищем компанию по owner
    company = Company.objects.filter(owner=admin).first()
    
    if not company and admin_company_name:
        # Пробуем найти компанию по названию
        company = Company.objects.filter(name=admin_company_name).first()
    
    if company:
        # Обновляем поле company у пользователя
        if admin.company != company:
            admin.company = company
            admin.save()
            print(f"   ✅ Обновлена связь user.company для {admin.username}: {company.name}")
            updated_users += 1
    else:
        print(f"   ⚠️ {admin.username}: компания не найдена (company_name={admin_company_name})")

# Проверяем CompanyBalance и связываем с company
print("\n" + "-" * 80)
print("Проверка CompanyBalance...")

balances = CompanyBalance.objects.all()
updated_balances = 0
for balance in balances:
    if balance.company_name and not balance.company:
        # Ищем компанию по названию
        company = Company.objects.filter(name=balance.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=balance.company_name).first()
        
        if company:
            balance.company = company
            balance.save()
            updated_balances += 1
            print(f"   ✅ Обновлён баланс для {company.name}")

print(f"Обновлено балансов: {updated_balances}")

# Проверяем Student
print("\n" + "-" * 80)
print("Проверка студентов...")

students = Student.objects.all()
updated_students = 0
for student in students:
    if student.company_name and not student.company:
        company = Company.objects.filter(name=student.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=student.company_name).first()
        
        if company:
            student.company = company
            student.save()
            updated_students += 1

print(f"   ✅ Обновлено студентов: {updated_students}")

# Проверяем Group
print("\n" + "-" * 80)
print("Проверка групп...")

groups = Group.objects.all()
updated_groups = 0
for group in groups:
    if group.company_name and not group.company:
        company = Company.objects.filter(name=group.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=group.company_name).first()
        
        if company:
            group.company = company
            group.save()
            updated_groups += 1

print(f"   ✅ Обновлено групп: {updated_groups}")

# Проверяем Task
print("\n" + "-" * 80)
print("Проверка задач...")

tasks = Task.objects.all()
updated_tasks = 0
for task in tasks:
    if task.company_name and not task.company:
        company = Company.objects.filter(name=task.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=task.company_name).first()
        
        if company:
            task.company = company
            task.save()
            updated_tasks += 1

print(f"   ✅ Обновлено задач: {updated_tasks}")

# Проверяем TrialLead
print("\n" + "-" * 80)
print("Проверка тест-драйв лидов...")

trial_leads = TrialLead.objects.all()
updated_leads = 0
for lead in trial_leads:
    if lead.company_name and not lead.company:
        company = Company.objects.filter(name=lead.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=lead.company_name).first()
        
        if company:
            lead.company = company
            lead.save()
            updated_leads += 1

print(f"   ✅ Обновлено лидов: {updated_leads}")

# Проверяем Auditorium
print("\n" + "-" * 80)
print("Проверка аудиторий...")

auditoriums = Auditorium.objects.all()
updated_auditoriums = 0
for auditorium in auditoriums:
    if auditorium.company_name and not auditorium.company:
        company = Company.objects.filter(name=auditorium.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=auditorium.company_name).first()
        
        if company:
            auditorium.company = company
            auditorium.save()
            updated_auditoriums += 1

print(f"   ✅ Обновлено аудиторий: {updated_auditoriums}")

# Проверяем LandingPage
print("\n" + "-" * 80)
print("Проверка лендингов...")

landing_pages = LandingPage.objects.all()
updated_landings = 0
for page in landing_pages:
    if page.company_name and not page.company:
        company = Company.objects.filter(name=page.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=page.company_name).first()
        
        if company:
            page.company = company
            page.save()
            updated_landings += 1

print(f"   ✅ Обновлено лендингов: {updated_landings}")

# Проверяем HomeworkTask
print("\n" + "-" * 80)
print("Проверка домашних заданий...")

homework_tasks = HomeworkTask.objects.all()
updated_homeworks = 0
for hw in homework_tasks:
    if hw.company_name and not hw.company:
        company = Company.objects.filter(name=hw.company_name).first()
        if not company:
            company = Company.objects.filter(owner__company_name=hw.company_name).first()
        
        if company:
            hw.company = company
            hw.save()
            updated_homeworks += 1

print(f"   ✅ Обновлено домашних заданий: {updated_homeworks}")

print("\n" + "=" * 80)
print("ИТОГИ")
print("=" * 80)
print(f"Обновлено пользователей (course_admin): {updated_users}")
print(f"Обновлено балансов: {updated_balances}")
print(f"Обновлено студентов: {updated_students}")
print(f"Обновлено групп: {updated_groups}")
print(f"Обновлено задач: {updated_tasks}")
print(f"Обновлено лидов: {updated_leads}")
print(f"Обновлено аудиторий: {updated_auditoriums}")
print(f"Обновлено лендингов: {updated_landings}")
print(f"Обновлено домашних заданий: {updated_homeworks}")
print("=" * 80)

# Выводим итоговую статистику по компаниям
print("\n" + "=" * 80)
print("ИТОГОВАЯ СТАТИСТИКА ПО КОМПАНИЯМ")
print("=" * 80)

companies = Company.objects.all()
for company in companies:
    students_count = company.students.count() if company.students else 0
    groups_count = company.groups.count() if company.groups else 0
    tasks_count = company.tasks.count() if company.tasks else 0
    trial_leads_count = company.trial_leads.count() if company.trial_leads else 0
    auditoriums_count = company.auditoriums.count() if company.auditoriums else 0
    landing_pages_count = company.landing_pages.count() if company.landing_pages else 0
    balance = company.balance.balance if hasattr(company, 'balance') and company.balance else 0
    
    print(f"\n🏢 {company.name}")
    print(f"   Владелец: {company.owner.username if company.owner else '—'}")
    print(f"   Студентов: {students_count}")
    print(f"   Групп: {groups_count}")
    print(f"   Задач: {tasks_count}")
    print(f"   Тест-драйв лидов: {trial_leads_count}")
    print(f"   Аудиторий: {auditoriums_count}")
    print(f"   Лендингов: {landing_pages_count}")
    print(f"   Баланс: {balance} eduCoins")

print("\n" + "=" * 80)