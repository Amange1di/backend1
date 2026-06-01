import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, Course, Group, Student, Attendance, Payment, TrialLead

# Получаем компанию
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания не найдена!")
    exit(1)

admin = User.objects.filter(username='admin_smartkids').first()
if not admin:
    print("❌ Админ не найден!")
    exit(1)

print("="*60)
print(f"Заполнение данных для: {company.name}")
print("="*60)

# 1. Создаем профили студентов из User
users_students = User.objects.filter(company=company, role=User.Role.STUDENT)
for user in users_students:
    student, created = Student.objects.get_or_create(
        user=user,
        defaults={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone or '',
            'company': company,
            'company_name': company.name,
        }
    )
    if created:
        print(f"✅ Профиль студента создан: {student}")
    else:
        student.first_name = user.first_name
        student.last_name = user.last_name
        student.phone = user.phone or ''
        student.company = company
        student.company_name = company.name
        student.save()

print(f"\n✅ Профили студентов: {Student.objects.filter(company=company).count()}")

# 2. Создаем группы для каждого курса
courses = Course.objects.filter(admins=admin)
groups_created = 0
for course in courses:
    for i in range(2):
        group_name = f"{course.title[:20]} - Группа {i+1}"
        group, created = Group.objects.get_or_create(
            name=group_name,
            course=course,
            company=company,
            defaults={
                'start_date': date.today(),
            }
        )
        if created:
            groups_created += 1
            print(f"✅ Группа создана: {group}")

print(f"\n✅ Создано групп: {groups_created}")

# 3. Распределяем студентов по группам и назначаем основные курсы
students = Student.objects.filter(company=company)
groups = Group.objects.filter(company=company)

students_assigned = 0
for idx, student in enumerate(students):
    if groups.exists():
        primary_group = groups[idx % groups.count()]
        student.primary_course = primary_group.course
        student.save()
        students_assigned += 1

print(f"✅ Студентов назначено на курсы: {students_assigned}")

# 4. Создаем тестовую посещаемость (последние 7 дней)
attendance_created = 0
for student in students[:10]:
    for i in range(3):
        att_date = date.today() - timedelta(days=i*2)
        group = groups[0] if groups else None
        
        if group:
            att, created = Attendance.objects.get_or_create(
                group=group,
                student=student,
                date=att_date,
                defaults={'status': Attendance.Status.PRESENT}
            )
            if created:
                attendance_created += 1

print(f"✅ Записей посещаемости: {attendance_created}")

# 5. Создаем тестовые платежи
payments_created = 0
for student in students[:5]:
    if groups:
        payment, created = Payment.objects.get_or_create(
            student=student,
            group=groups[0],
            amount=2500,
            status=Payment.Status.PAID,
            defaults={
                'company': company,
                'paid_at': date.today(),
            }
        )
        if created:
            payments_created += 1
            print(f"✅ Платеж: {student} - 2500 сом")

print(f"\n✅ Платежей создано: {payments_created}")

# 6. Проверяем заявки
leads = TrialLead.objects.filter(company=company)
print(f"\nℹ️ Заявок (leads): {leads.count()}")

# 7. Создаем привязки учителей к курсам (добавляем в admins курса)
teachers = User.objects.filter(company=company, role=User.Role.TEACHER)
teacher_courses_created = 0
courses_list = list(courses)

for idx, teacher_user in enumerate(teachers):
    if courses_list:
        course = courses_list[idx % len(courses_list)]
        # Добавляем учителя в admins курса
        course.admins.add(teacher_user)
        teacher_courses_created += 1
        print(f"✅ Учитель назначен: {teacher_user.first_name} {teacher_user.last_name} -> {course.title}")

print(f"\n✅ Назначений учителей: {teacher_courses_created}")

print("\n" + "="*60)
print("ИТОГОВЫЕ ДАННЫЕ:")
print("="*60)
print(f"Компания: {company.name}")
print(f"Курсы: {courses.count()}")
print(f"Учителя: {teachers.count()}")
print(f"Студенты: {students.count()}")
print(f"Группы: {groups.count()}")
print(f"Посещаемость: {attendance_created}")
print(f"Платежи: {payments_created}")
print(f"Заявки: {leads.count()}")

print("\n✅ Все таблицы заполнены!")
print("\nЛогин: admin_smartkids / admin123")
