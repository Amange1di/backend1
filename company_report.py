import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Company, User, Student, Group, Course, Task, TrialLead, Group

print("=" * 80)
print("ОТЧЁТ ПО ВСЕМ КОМПАНИЯМ")
print("=" * 80)

companies = Company.objects.all()
print(f"\nВсего компаний: {companies.count()}")
print("-" * 80)

total_students = 0
total_managers = 0
total_teachers = 0
total_groups = 0
total_courses = 0
total_vacancies = 0
total_trial_leads = 0
total_pending_tasks = 0

for company in companies:
    print(f"\n🏢 {company.name}")
    print(f"   Slug: {company.slug}")
    print(f"   Категория: {company.get_category_display()}")
    print(f"   Город: {company.get_city_display()}")
    print(f"   Статус: {'Активна' if company.is_active else 'Неактивна'}")
    print(f"   Рейтинг: {company.rating}/5 ({company.reviews_count} отзывов)")
    print(f"   Владелец: {company.owner.username} ({company.owner.email})")
    
    # Студенты
    students_count = company.students.count()
    total_students += students_count
    print(f"   📚 Студентов: {students_count}")
    
    # Менеджеры
    managers_count = company.users.filter(role=User.Role.MANAGER).count()
    total_managers += managers_count
    print(f"   👥 Менеджеров: {managers_count}")
    
    # Учителя
    teachers_count = company.users.filter(role=User.Role.TEACHER).count()
    total_teachers += teachers_count
    print(f"   👨‍🏫 Учителей: {teachers_count}")
    
    # Course admins
    course_admins_count = company.users.filter(role=User.Role.COURSE_ADMIN).count()
    print(f"   👔 Course Admins: {course_admins_count}")
    
    # Группы
    groups_count = company.groups.count()
    total_groups += groups_count
    print(f"   📋 Групп: {groups_count}")
    
    # Курсы
    courses_count = Course.objects.filter(admins=company.owner).count()
    total_courses += courses_count
    print(f"   📖 Курсов: {courses_count}")
    
    # Вакансии
    vacancies_count = company.vacancies.filter(is_active=True).count()
    total_vacancies += vacancies_count
    print(f"   💼 Вакансий (активных): {vacancies_count}")
    
    # Заявки от учителей
    teacher_applications_count = company.teacher_applications.count()
    print(f"   📨 Заявок от учителей: {teacher_applications_count}")
    
    # Заявки от студентов
    student_applications_count = company.student_applications.count()
    print(f"   📨 Заявок от студентов: {student_applications_count}")
    
    # Тест-драйв лиды
    trial_leads_count = company.trial_leads.count()
    total_trial_leads += trial_leads_count
    print(f"   🎯 Тест-драйв лидов: {trial_leads_count}")
    
    # Задачи
    tasks_count = company.tasks.count()
    pending_tasks = company.tasks.filter(status=Task.Status.PENDING).count()
    total_pending_tasks += pending_tasks
    print(f"   ✅ Задач (всего/ожидание): {tasks_count}/{pending_tasks}")
    
    # Баланс
    if hasattr(company, 'balance'):
        print(f"   💰 Баланс: {company.balance.balance} eduCoins")
    
    # Аудитории
    auditoriums_count = company.auditoriums.count()
    print(f"   🏛️ Аудиторий: {auditoriums_count}")
    
    # Лендинги
    landing_pages_count = company.landing_pages.count()
    active_landing_pages = company.landing_pages.filter(status='active').count()
    print(f"   🌐 Лендингов (всего/активные): {landing_pages_count}/{active_landing_pages}")

print("\n" + "=" * 80)
print("ОБЩАЯ СТАТИСТИКА")
print("=" * 80)
print(f"Всего компаний:           {companies.count()}")
print(f"Всего студентов:          {total_students}")
print(f"Всего менеджеров:         {total_managers}")
print(f"Всего учителей:           {total_teachers}")
print(f"Всего групп:              {total_groups}")
print(f"Всего курсов:             {total_courses}")
print(f"Всего вакансий (активных): {total_vacancies}")
print(f"Всего тест-драйв лидов:   {total_trial_leads}")
print(f"Всего задач (ожидание):   {total_pending_tasks}")
print("=" * 80)