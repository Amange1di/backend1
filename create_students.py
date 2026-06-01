import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company, Group
import random

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
groups = Group.objects.filter(company=company)
print(f"Компания: {company.name}")
print(f"Групп: {groups.count()}")
print()

# Имена на кыргызском (60%)
kyrgyz_first_names = [
    "Айбек", "Бакыт", "Дастан", "Эркин", "Талант", "Азамат", "Нурлан", "Бекзат",
    "Айсулуу", "Гульназ", "Роза", "Нуржан", "Кайыргүл", "Айпинде", "Жаныш", "Тогрул",
    "Азамат", "Бекболот", "Данияр", "Каныбек", "Мурат", "Омор", "Паркент", "Рустам",
    "Саякбай", "Токтогул", "Улан", "Чынгыз", "Айгуль", "Бакытгуль", "Айпери", "Гульнар",
    "Дилара", "Эльмира", "Жанар", "Камшат", "Лейла", "Мадина", "Нигара", "Ольга"
]

# Фамилии на кыргызском
kyrgyz_last_names = [
    "Караев", "Алиев", "Усенов", "Мамытов", "Ибраимов", "Токтогулов", "Садыкова",
    "Жумабеков", "Кожобекова", "Асанов", "Искакова", "Матраимов", "Эркинова",
    "Кудайбердиев", "Абдылдаев", "Алиева", "Караева", "Асанова", "Искакова",
    "Садыков", "Жумабеков", "Мамытов", "Токтогулов", "Алиев", "Караев"
]

# Имена на русском (10%)
russian_first_names = [
    "Александр", "Дмитрий", "Максим", "Сергей", "Андрей", "Алексей", "Игорь", "Олег",
    "Елена", "Ольга", "Татьяна", "Наталья", "Ирина", "Анна", "Мария", "Екатерина"
]

russian_last_names = [
    "Иванов", "Петров", "Сидоров", "Смирнов", "Козлов", "Новиков", "Фёдоров",
    "Морозов", "Волков", "Алексеев", "Иванова", "Петрова", "Сидорова", "Смирнова"
]

# Имена на узбекском (30%)
uzbek_first_names = [
    "Азамат", "Бекзод", "Дилшод", "Эркин", "Талант", "Абдулла", "Рустам", "Шухрат",
    "Мадина", "Гулнора", "Диёра", "Нигара", "Фарида", "Зулайхо", "Наргиз", "Садридин",
    "Бехзод", "Жахонгир", "Илхом", "Камил", "Лутфулла", "Мурод", "Отабек", "Парвиз"
]

uzbek_last_names = [
    "Каримов", "Абдуллаев", "Рустамов", "Икрамов", "Турсунов", "Алимов", "Усмонов",
    "Жалилов", "Саидов", "Нуров", "Каримова", "Абдуллаева", "Рустамова", "Ибрагимов"
]

# Генерация email
def generate_email(first_name, last_name, unique_id):
    clean_first = ''.join(c for c in first_name.lower() if c.isalpha())
    clean_last = ''.join(c for c in last_name.lower() if c.isalpha())
    return f"{clean_first}.{clean_last}{unique_id}@edupro.kg"

# Создание студентов
created_count = 0
total_students = 0
global_student_index = 1

for group in groups:
    # Количество студентов для этой группы (5-10 случайное)
    students_count = random.randint(5, 10)
    
    print(f"\n📚 Группа: {group.name}")
    print(f"  Создаём студентов: {students_count}")
    
    # Распределение по языкам: 60% кыргызские, 10% русские, 30% узбекские
    kyrgyz_count = int(students_count * 0.6)
    russian_count = int(students_count * 0.1)
    uzbek_count = students_count - kyrgyz_count - russian_count
    
    # Создаём кыргызских студентов
    for i in range(kyrgyz_count):
        first_name = random.choice(kyrgyz_first_names)
        last_name = random.choice(kyrgyz_last_names)
        username = generate_email(first_name, last_name, global_student_index)
        
        student = User.objects.create(
            username=username,
            email=username,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.STUDENT,
            company=company,
            phone=f"+996555{random.randint(100000, 999999)}",
            is_active=True,
            must_set_password=False,
        )
        print(f"  ✅ {first_name} {last_name} (@{student.username})")
        global_student_index += 1
        created_count += 1
        total_students += 1
    
    # Создаём русских студентов
    for i in range(russian_count):
        first_name = random.choice(russian_first_names)
        last_name = random.choice(russian_last_names)
        username = generate_email(first_name, last_name, global_student_index)
        
        student = User.objects.create(
            username=username,
            email=username,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.STUDENT,
            company=company,
            phone=f"+770{random.randint(1000000, 9999999)}",
            is_active=True,
            must_set_password=False,
        )
        print(f"  ✅ {first_name} {last_name} (@{student.username})")
        global_student_index += 1
        created_count += 1
        total_students += 1
    
    # Создаём узбекских студентов
    for i in range(uzbek_count):
        first_name = random.choice(uzbek_first_names)
        last_name = random.choice(uzbek_last_names)
        username = generate_email(first_name, last_name, global_student_index)
        
        student = User.objects.create(
            username=username,
            email=username,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.STUDENT,
            company=company,
            phone=f"+9989{random.randint(1000000, 9999999)}",
            is_active=True,
            must_set_password=False,
        )
        print(f"  ✅ {first_name} {last_name} (@{student.username})")
        global_student_index += 1
        created_count += 1
        total_students += 1

print(f"\n{'='*50}")
print(f"✅ Создано студентов: {total_students}")
print(f"{'='*50}")

# Проверка
students = User.objects.filter(role=User.Role.STUDENT, company=company)
print(f"\nВсего студентов в компании: {students.count()}")

# Проверка по языкам
kyrgyz_students = students.filter(first_name__in=kyrgyz_first_names[:10])
russian_students = students.filter(first_name__in=russian_first_names[:5])
uzbek_students = students.filter(first_name__in=uzbek_first_names[:10])

print(f"Кыргызские имена: ~{int(total_students * 0.6)}")
print(f"Русские имена: ~{int(total_students * 0.1)}")
print(f"Узбекские имена: ~{int(total_students * 0.3)}")
