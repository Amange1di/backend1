import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Student, User, Company, Group, Course

company = Company.objects.filter(slug='smart-kids-center').first()
students = Student.objects.filter(company=company)

print('Проверка связей студентов:')
print(f'Всего студентов: {students.count()}')

# Студенты с primary_course
with_course = students.exclude(primary_course__isnull=True)
print(f'С primary_course: {with_course.count()}')

# Студенты с группами
with_groups = students.filter(groups__isnull=False).distinct()
print(f'С группами: {with_groups.count()}')

# Проверка компаний в курсах и группах
for student in students[:5]:
    print(f'\n{student.first_name} {student.last_name}:')
    if student.primary_course:
        print(f'  primary_course: {student.primary_course.title}')
        print(f'  course.company: {student.primary_course.company_name}')
    groups = student.groups.all()
    if groups.exists():
        for g in groups:
            print(f'  group: {g.name}, company: {g.company_name}')

# Фильтр для менеджера (как в API)
import django.db.models as models
user = User.objects.filter(username='manager_smartkids_1').first()
filtered = students.filter(
    models.Q(company_name=user.company_name)
    | models.Q(primary_course__admins__company_name=user.company_name)
    | models.Q(groups__company_name=user.company_name)
).distinct()

print(f'\nФильтр API для менеджера: {filtered.count()} студентов')