import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company

# Получаем компанию Smart Kids Center
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания Smart Kids Center не найдена!")
    exit(1)

# Уникальные имена с распределением
KYRGYZ_MALE = ['Айбек', 'Бакыт', 'Талант', 'Азамат', 'Нурлан', 'Данияр', 'Эркин', 'Каныбек', 'Жаныбек', 'Рустам', 'Айдар', 'Азат', 'Бердибек', 'Дастан', 'Эдиге']
KYRGYZ_FEMALE = ['Айша', 'Нурзат', 'Айым', 'Гульнара', 'Дилара', 'Саида', 'Айсулуу', 'Айгерим', 'Назик', 'Бакытжан', 'Каныкей', 'Роза', 'Садыра', 'Эльмира', 'Фарида']

RUSSIAN_MALE = ['Алексей', 'Дмитрий', 'Сергей', 'Игорь', 'Андрей', 'Максим', 'Александр', 'Владимир', 'Павел', 'Олег']
RUSSIAN_FEMALE = ['Анна', 'Елена', 'Ольга', 'Татьяна', 'Наталья', 'Марина', 'Ирина', 'Екатерина', 'Светлана', 'Юлия']

UZBEK_MALE = ['Азиз', 'Фарход', 'Рустам', 'Шухрат', 'Вадим', 'Тимур', 'Дилшод', 'Бахтиёр', 'Хуршед', 'Самандар']
UZBEK_FEMALE = ['Гульнора', 'Зарина', 'Мадина', 'Сабрина', 'Диана', 'Нигина', 'Шahnoz', 'Мехриноз', 'Рано', 'Фотима']

# Плейсхолдеры для проверки уникальности
used_names = {}

def get_unique_name(names_list, max_repeats=3):
    """Получить уникальное имя (не более max_repeats повторений)"""
    available = [name for name in names_list if used_names.get(name, 0) < max_repeats]
    
    if not available:
        # Если все имена использованы слишком много раз, сбрасываем счетчик
        used_names.clear()
        available = names_list
    
    name = random.choice(available)
    used_names[name] = used_names.get(name, 0) + 1
    return name

def generate_student_name(gender='mixed'):
    """Генерировать ФИО студента"""
    if gender == 'male':
        first_name = get_unique_name(KYRGYZ_MALE + RUSSIAN_MALE + UZBEK_MALE)
        last_names = ['Алиев', 'Исаков', 'Раимов', 'Усенов', 'Абдыров', 'Петров', 'Иванов', 'Каримов', 'Ахмедов', 'Садыков']
    elif gender == 'female':
        first_name = get_unique_name(KYRGYZ_FEMALE + RUSSIAN_FEMALE + UZBEK_FEMALE)
        last_names = ['Алиева', 'Исакова', 'Раимова', 'Усенова', 'Абдырова', 'Петрова', 'Иванова', 'Каримова', 'Ахмедова', 'Садыкова']
    else:
        if random.random() < 0.5:
            return generate_student_name('male')
        else:
            return generate_student_name('female')
    
    last_name = random.choice(last_names)
    return first_name, last_name

# Создаем 30 студентов (для распределения 60/10/30)
students_config = []

# 60% кыргызские (18 студентов)
for i in range(18):
    gender = 'male' if i % 2 == 0 else 'female'
    first_name, last_name = generate_student_name(gender)
    students_config.append({
        'first_name': first_name,
        'last_name': last_name,
        'phone': f'+99670{300000 + i:06d}',
    })

# 10% русские (3 студента)
for i in range(3):
    gender = 'male' if i % 2 == 0 else 'female'
    first_name, last_name = generate_student_name(gender)
    students_config.append({
        'first_name': first_name,
        'last_name': last_name,
        'phone': f'+99670{400000 + i:06d}',
    })

# 30% узбекские (9 студентов)
for i in range(9):
    gender = 'male' if i % 2 == 0 else 'female'
    first_name, last_name = generate_student_name(gender)
    students_config.append({
        'first_name': first_name,
        'last_name': last_name,
        'phone': f'+99670{500000 + i:06d}',
    })

# Создаем студентов
print("="*50)
print("Создание студентов Smart Kids Center")
print("="*50)

created_count = 0
for idx, student_data in enumerate(students_config):
    username = f'student_{student_data["first_name"].lower()}_{student_data["last_name"].lower()}'[:50]
    
    student, created = User.objects.get_or_create(
        username=username,
        defaults={
            'role': User.Role.STUDENT,
            'first_name': student_data['first_name'],
            'last_name': student_data['last_name'],
            'company': company,
            'company_name': company.name,
            'phone': student_data['phone'],
        }
    )
    
    if created:
        student.set_password('admin123')
        student.save()
        print(f"✅ Студент {idx+1}: {student_data['first_name']} {student_data['last_name']} ({student_data['phone']})")
        created_count += 1
    else:
        print(f"ℹ️ Уже существует: {student_data['first_name']} {student_data['last_name']}")

print("\n" + "="*50)
print(f"✅ Создано {created_count} студентов!")
print("="*50)
print("\nРаспределение имен:")
print(f"  Кыргызские: 18 (60%)")
print(f"  Русские: 3 (10%)")
print(f"  Узбекские: 9 (30%)")
print(f"\nЛогин: student_... / admin123")
