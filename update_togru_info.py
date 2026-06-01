import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import User

# Находим преподавателя
teacher = User.objects.get(username="togru.abdyldayev")
print(f"Обновление данных для: {teacher.username}")

# Обновляем информацию
teacher.first_name = "Тогрул"
teacher.last_name = "Абдылдаев"
teacher.phone = "+996555100015"
teacher.email = "togru.abdyldayev@edupro.kg"
teacher.telegram = "@togru_abdyldayev"
teacher.working_hours = "Пн-Пт 09:00-18:00"
teacher.color = "#45B2EF"
teacher.address = "г. Бишкек, ул. Токтогула 123"
teacher.salary_rate = 5000
teacher.save()

print(f"✅ Данные обновлены:")
print(f"   Имя: {teacher.first_name} {teacher.last_name}")
print(f"   Телефон: {teacher.phone}")
print(f"   Email: {teacher.email}")
print(f"   Telegram: {teacher.telegram}")
print(f"   Часы работы: {teacher.working_hours}")
print(f"   Цвет: {teacher.color}")
print(f"   Адрес: {teacher.address}")
print(f"   Ставка зарплаты: {teacher.salary_rate} сом")

# Показываем курсы
from core.models import Course
courses = teacher.admin_courses.all()
print(f"\n📚 Курсы ({courses.count()}):")
for course in courses:
    print(f"   • {course.title}")
