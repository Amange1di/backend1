import os
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()

from core.models import Company, User, Task

company = Company.objects.get(name='Edu Center Pro')
admin = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).order_by('id').first()
managers = list(User.objects.filter(role=User.Role.MANAGER, company=company, is_active=True).order_by('id'))
if not admin or not managers:
    raise SystemExit('admin/managers not found')

Task.objects.filter(company=company).delete()

start = date(2026, 3, 1)
end = date(2026, 5, 31)

titles = [
    'Обзвон лидов',
    'Проверка оплат студентов',
    'Подтвердить расписание группы',
    'Сбор обратной связи',
    'Актуализация базы студентов',
    'Контроль посещаемости группы',
    'Подготовка отчета по группе',
    'Связаться с должниками',
    'Проверка домашних заданий',
    'Согласование пробного урока',
]

statuses = [Task.Status.PENDING, Task.Status.IN_PROGRESS, Task.Status.COMPLETED]
priorities = [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH]

created = 0
cur = start
while cur <= end:
    if cur.weekday() in (0, 3):
        for _ in range(2):
            manager = random.choice(managers)
            title = random.choice(titles)
            Task.objects.create(
                title=title,
                description=f"{title}. Дата выполнения: {cur.isoformat()}",
                assigned_to=manager,
                created_by=admin,
                company=company,
                company_name=company.name,
                due_date=cur,
                status=random.choices(statuses, weights=[0.5, 0.3, 0.2], k=1)[0],
                priority=random.choices(priorities, weights=[0.25, 0.55, 0.20], k=1)[0],
                repeat_type=Task.RepeatType.NONE,
            )
            created += 1
    cur += timedelta(days=1)

print('CREATED', created)
first = Task.objects.filter(company=company).order_by('id').first()
print('FIRST_TITLE', first.title if first else None)
