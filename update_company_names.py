import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company, Student, Group, Task, TrialLead, Auditorium, LandingPage, HomeworkTask, CompanyBalance

print("=" * 80)
print("ОБНОВЛЕНИЕ company_name ДЛЯ СОВМЕСТИМОСТИ")
print("=" * 80)

updated_users = 0
updated_students = 0
updated_groups = 0
updated_tasks = 0
updated_leads = 0
updated_auditoriums = 0
updated_landings = 0
updated_homeworks = 0
updated_balances = 0

# Обновляем пользователей
print("\n🔄 Обновление пользователей...")
for user in User.objects.all():
    if user.company and user.company.name != user.company_name:
        user.company_name = user.company.name
        user.save(update_fields=['company_name'])
        updated_users += 1
        print(f"   ✅ {user.username}: {user.company_name}")

# Обновляем студентов
print("\n🔄 Обновление студентов...")
for student in Student.objects.all():
    if student.company and student.company.name != student.company_name:
        student.company_name = student.company.name
        student.save(update_fields=['company_name'])
        updated_students += 1

# Обновляем группы
print("\n🔄 Обновление групп...")
for group in Group.objects.all():
    if group.company and group.company.name != group.company_name:
        group.company_name = group.company.name
        group.save(update_fields=['company_name'])
        updated_groups += 1

# Обновляем задачи
print("\n🔄 Обновление задач...")
for task in Task.objects.all():
    if task.company and task.company.name != task.company_name:
        task.company_name = task.company.name
        task.save(update_fields=['company_name'])
        updated_tasks += 1

# Обновляем лиды
print("\n🔄 Обновление тест-драйв лидов...")
for lead in TrialLead.objects.all():
    if lead.company and lead.company.name != lead.company_name:
        lead.company_name = lead.company.name
        lead.save(update_fields=['company_name'])
        updated_leads += 1

# Обновляем аудитории
print("\n🔄 Обновление аудиторий...")
for auditorium in Auditorium.objects.all():
    if auditorium.company and auditorium.company.name != auditorium.company_name:
        auditorium.company_name = auditorium.company.name
        auditorium.save(update_fields=['company_name'])
        updated_auditoriums += 1

# Обновляем лендинги
print("\n🔄 Обновление лендингов...")
for page in LandingPage.objects.all():
    if page.company and page.company.name != page.company_name:
        page.company_name = page.company.name
        page.save(update_fields=['company_name'])
        updated_landings += 1

# Обновляем домашние задания
print("\n🔄 Обновление домашних заданий...")
for hw in HomeworkTask.objects.all():
    if hw.company and hw.company.name != hw.company_name:
        hw.company_name = hw.company.name
        hw.save(update_fields=['company_name'])
        updated_homeworks += 1

# Обновляем балансы
print("\n🔄 Обновление CompanyBalance...")
for balance in CompanyBalance.objects.all():
    if balance.company and balance.company.name != balance.company_name:
        balance.company_name = balance.company.name
        balance.save(update_fields=['company_name'])
        updated_balances += 1

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)
print(f"Обновлено пользователей: {updated_users}")
print(f"Обновлено студентов: {updated_students}")
print(f"Обновлено групп: {updated_groups}")
print(f"Обновлено задач: {updated_tasks}")
print(f"Обновлено лидов: {updated_leads}")
print(f"Обновлено аудиторий: {updated_auditoriums}")
print(f"Обновлено лендингов: {updated_landings}")
print(f"Обновлено домашних заданий: {updated_homeworks}")
print(f"Обновлено CompanyBalance: {updated_balances}")
print("=" * 80)