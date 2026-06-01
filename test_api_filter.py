import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, Course, Student

# Получаем менеджера
manager = User.objects.filter(username='manager_smartkids_1').first()
print(f"Менеджер: {manager.username if manager else 'Не найден'}")
print(f"company: {manager.company if manager else None}")
print(f"company_name: {manager.company_name if manager else None}")

# Тестируем фильтрацию
if manager:
    print("\n=== Тест фильтрации через Django ORM ===")
    
    # Курсы
    courses = Course.objects.filter(admins__company=manager.company).distinct()
    print(f"\nКурсы через company: {courses.count()}")
    for c in courses:
        print(f"  - {c.title}")
    
    # Учителя
    teachers = User.objects.filter(role=User.Role.TEACHER, company=manager.company)
    print(f"\nУчителя через company: {teachers.count()}")
    
    # Студенты
    students = Student.objects.filter(company=manager.company)
    print(f"\nСтуденты через company: {students.count()}")
    
    # Через company_name (старый способ)
    courses_old = Course.objects.filter(admins__company_name=manager.company_name).distinct()
    print(f"\nКурсы через company_name (старый): {courses_old.count()}")
    
    students_old = Student.objects.filter(company_name=manager.company_name)
    print(f"Студенты через company_name (старый): {students_old.count()}")
