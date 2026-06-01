import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Course, Company, Group
from datetime import date

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
admin = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).first()

if not admin:
    print("Course Admin не найден!")
    exit(1)

company_courses = list(admin.admin_courses.all())
print(f"Компания: {company.name}")
print(f"Курсов: {len(company_courses)}")
print()

# Месяцы для создания групп (для дат)
months_data = [
    ("Март 2026", date(2026, 3, 1), date(2026, 3, 31)),
    ("Апрель 2026", date(2026, 4, 1), date(2026, 4, 30)),
    ("Май 2026", date(2026, 5, 1), date(2026, 5, 31)),
]

# Расписание дней (для разных групп разные дни)
schedule_days_options = [
    "пн, ср, пт",  # понедельник, среда, пятница
    "вт, чт, сб",  # вторник, четверг, суббота
    "пн, вт, чт",  # понедельник, вторник, четверг
]

# Время занятий для разных групп
schedule_times = ["10:00", "14:00", "18:00"]

created_count = 0

for course_idx, course in enumerate(company_courses):
    # Получаем преподавателей для этого курса
    teachers = [u for u in course.admins.all() if u.role == User.Role.TEACHER]
    
    if not teachers:
        print(f"⚠️  {course.title}: Нет преподавателей, пропускаем")
        continue
    
    # Определяем количество групп для этого курса (2-3)
    if course_idx < 4:
        groups_count = 3  # Первые 4 курса по 3 группы
    else:
        groups_count = 2  # Остальные по 2 группы
    
    print(f"\n📚 {course.title}")
    print(f"  Преподаватели: {[f'{t.first_name} {t.last_name}' for t in teachers]}")
    print(f"  Создаём групп: {groups_count}")
    
    for group_idx in range(groups_count):
        # Выбираем месяц (для дат)
        month_name, month_start, month_end = months_data[group_idx % len(months_data)]
        
        # Выбираем преподавателя (чередование)
        teacher = teachers[group_idx % len(teachers)]
        
        # Выбираем расписание
        schedule_days = schedule_days_options[group_idx % len(schedule_days_options)]
        schedule_time = schedule_times[group_idx % len(schedule_times)]
        
        # Название группы: "Бизнес-английский-1", "Бизнес-английский-2" и т.д.
        group_number = group_idx + 1
        group_name = f"{course.title}-{group_number}"
        
        # Количество уроков (примерно: 3 раза в неделю * 4 недели = 12 уроков)
        lessons_count = 12
        
        # Создаём группу
        group = Group.objects.create(
            name=group_name,
            course=course,
            teacher=teacher,
            company=company,
            schedule_days=schedule_days,
            schedule_time=schedule_time,
            lessons_count=lessons_count,
            start_date=month_start,
            end_date=month_end,
            is_login_allowed=True,
        )
        
        print(f"  ✅ Группа: {group.name}")
        print(f"     Преподаватель: {teacher.first_name} {teacher.last_name}")
        print(f"     Расписание: {schedule_days} в {schedule_time}")
        print(f"     Период: {month_start} - {month_end}")
        
        created_count += 1

print(f"\n{'='*50}")
print(f"✅ Создано групп: {created_count}")
print(f"{'='*50}")

# Проверка
print(f"\nПроверка всех групп для {company.name}:")
all_groups = Group.objects.filter(company=company)
print(f"Всего групп: {all_groups.count()}")

for course in company_courses:
    course_groups = all_groups.filter(course=course)
    if course_groups.exists():
        print(f"\n  {course.title}: {course_groups.count()} групп")
        for g in course_groups:
            print(f"    - {g.name} ({g.start_date} - {g.end_date})")
