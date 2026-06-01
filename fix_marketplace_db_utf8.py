import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()

from core.models import Company, User, PublicCourse, JobVacancy

company = Company.objects.get(name='Edu Center Pro')
owner = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).order_by('id').first()

if owner and company.owner_id != owner.id:
    company.owner = owner
    company.save(update_fields=['owner'])

courses_ru = [
    ('Английский для начинающих (A1)', 'Базовый курс английского языка для начинающих.', 'Пн/Ср/Пт', 4000, 8),
    ('Английский средний уровень (B1)', 'Курс для уверенного общения и понимания английской речи.', 'Вт/Чт/Сб', 3000, 8),
    ('Подготовка к IELTS', 'Подготовка к IELTS: Reading, Listening, Writing, Speaking.', 'Пн/Ср/Пт', 3000, 10),
    ('Разговорный английский клуб', 'Практика разговорного английского в мини-группах.', 'Вт/Чт', 3500, 6),
    ('Python для начинающих', 'Основы программирования на Python с практическими заданиями.', 'Пн/Ср/Пт', 2500, 8),
    ('Основы Frontend-разработки', 'HTML, CSS, JavaScript и создание первых веб-страниц.', 'Вт/Чт/Сб', 3500, 8),
]

jobs_ru = [
    ('Преподаватель английского языка', 'Проведение занятий по английскому языку для групп разных уровней.'),
    ('Преподаватель IELTS', 'Подготовка студентов к международному экзамену IELTS.'),
    ('Преподаватель математики', 'Проведение уроков математики и подготовка к экзаменам.'),
    ('Ментор по Python', 'Обучение основам Python и проверка практических заданий.'),
    ('Академический менеджер', 'Контроль расписания, посещаемости и учебного процесса.'),
    ('SMM-менеджер', 'Ведение соцсетей, публикации и коммуникация с аудиторией.'),
]

courses = list(PublicCourse.objects.filter(company=company).order_by('id'))
for i, c in enumerate(courses):
    title, desc, sched, price, weeks = courses_ru[i % len(courses_ru)]
    c.title = title
    c.description = desc
    c.schedule = sched
    c.requirements = 'Базовые навыки работы с компьютером'
    c.price = price
    c.duration_weeks = weeks
    c.is_active = True
    c.save()

jobs = list(JobVacancy.objects.filter(company=company).order_by('id'))
for i, j in enumerate(jobs):
    title, desc = jobs_ru[i % len(jobs_ru)]
    j.title = title
    j.description = desc
    j.requirements = 'Опыт работы от 1 года, ответственность, коммуникабельность'
    j.responsibilities = 'Выполнение задач по должности, работа с командой и студентами'
    j.schedule = 'Полный рабочий день'
    j.city = 'osh'
    j.category = 'education'
    j.is_active = True
    j.save()

print('OWNER', company.owner.username if company.owner else None)
print('COURSES', PublicCourse.objects.filter(company=company, is_active=True).count())
print('JOBS', JobVacancy.objects.filter(company=company, is_active=True).count())
