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

print("="*60)
print(f"Дополнительные данные для: {company.name}")
print("="*60)

# Получаем существующие данные
groups = Group.objects.filter(company=company)
students = Student.objects.filter(company=company)
courses = Course.objects.filter(admins__username='admin_smartkids')

print(f"\n📊 Текущие данные:")
print(f"  Группы: {groups.count()}")
print(f"  Студенты: {students.count()}")
print(f"  Курсы: {courses.count()}")

# 1. Создаем посещаемость для последних 14 дней
print(f"\n📅 Создание посещаемости...")
attendance_created = 0
for group in groups:
    group_students = group.student_set.all() if hasattr(group, 'student_set') else students[:5]
    
    for i in range(14):
        att_date = date.today() - timedelta(days=i)
        
        for student in group_students:
            att, created = Attendance.objects.get_or_create(
                group=group,
                student=student,
                date=att_date,
                defaults={'status': Attendance.Status.PRESENT}
            )
            if created:
                attendance_created += 1

print(f"✅ Записей посещаемости создано: {attendance_created}")

# 2. Создаем платежи
print(f"\n💰 Создание платежей...")
payments_created = 0
for group in groups:
    group_students = group.student_set.all() if hasattr(group, 'student_set') else students[:5]
    
    for student in group_students:
        # Проверяем, есть ли уже платеж
        existing_payment = Payment.objects.filter(student=student, group=group).first()
        
        if not existing_payment:
            payment, created = Payment.objects.get_or_create(
                student=student,
                group=group,
                amount=2500,
                status=Payment.Status.PAID,
                defaults={
                    'company': company,
                    'paid_at': date.today() - timedelta(days=10),
                }
            )
            if created:
                payments_created += 1

print(f"✅ Платежей создано: {payments_created}")

# 3. Создаем тестовые заявки (leads)
print(f"\n📝 Создание заявок (leads)...")
leads_data = [
    ('Айгуль', 'Алиева', 8, 'Английский язык', 'Интересует запись ребенка на английский'),
    ('Бакыт', 'Исаков', 10, 'Программирование (Scratch)', 'Хочет научиться программировать'),
    ('Нурзат', 'Усенова', 7, 'Логика и математика', 'Развитие мышления'),
    ('Эльмир', 'Абдыров', 12, 'Python для детей', 'Интерес к программированию'),
    ('Саида', 'Раимова', 9, 'Английский язык', 'Подготовка к школе'),
    ('Талант', 'Козлов', 11, 'Программирование (Scratch)', 'Хобби'),
    ('Айым', 'Петрова', 6, 'Английский для детей', 'Раннее развитие'),
    ('Дилшод', 'Иванов', 13, 'Python для детей', 'Серьезный интерес'),
    ('Гульнара', 'Сидорова', 8, 'Логика и математика', 'Олимпиадная подготовка'),
    ('Азамат', 'Каримов', 10, 'Английский язык', 'Для путешествий'),
]

leads_created = 0
for first_name, last_name, age, course_interest, comment in leads_data:
    lead, created = TrialLead.objects.get_or_create(
        full_name=f'{first_name} {last_name}',
        company=company,
        defaults={
            'phone': f'+99670{600000 + leads_created:06d}',
            'age': age,
            'course_interest': course_interest,
            'comment': comment,
            'status': TrialLead.Status.NEW,
            'payment_status': TrialLead.PaymentStatus.NOT_PAID,
        }
    )
    if created:
        leads_created += 1
        print(f"  ✅ {first_name} {last_name} - {course_interest}")

print(f"\n✅ Заявок создано: {leads_created}")

# 4. Обновляем статус некоторых заявок
print(f"\n🔄 Обновление статусов заявок...")
leads = TrialLead.objects.filter(company=company)
updated = 0
for idx, lead in enumerate(leads):
    if idx < 3:
        lead.status = TrialLead.Status.CONTACTED
        lead.save()
        updated += 1
    elif idx < 6:
        lead.status = TrialLead.Status.TRIAL_SCHEDULED
        lead.trial_date = date.today() + timedelta(days=3)
        lead.save()
        updated += 1

print(f"✅ Статусов обновлено: {updated}")

print("\n" + "="*60)
print("ОБНОВЛЕННЫЕ ДАННЫЕ:")
print("="*60)
print(f"Компания: {company.name}")
print(f"Курсы: {courses.count()}")
print(f"Группы: {groups.count()}")
print(f"Студенты: {students.count()}")
print(f"Посещаемость: {Attendance.objects.filter(group__company=company).count()}")
print(f"Платежи: {Payment.objects.filter(company=company).count()}")
print(f"Заявки: {TrialLead.objects.filter(company=company).count()}")

print("\n✅ Все таблицы заполнены!")
print("\nЛогин: admin_smartkids / admin123")
