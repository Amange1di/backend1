import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Student

students = Student.objects.all()
print(f'Количество студентов: {students.count()}')
for s in students[:20]:
    print(f'  - {s.first_name} {s.last_name} ({s.phone})')

if students.count() > 20:
    print(f'  ... и ещё {students.count() - 20}')
