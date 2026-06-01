import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from core.models import Company, Group, Student

company_name = "Edu Center Pro"
company = Company.objects.filter(name=company_name).first()
if not company:
    raise SystemExit(f"Компания '{company_name}' не найдена")

groups = Group.objects.filter(company=company).order_by('id')
if not groups.exists():
    raise SystemExit(f"У компании '{company_name}' нет групп")

kyrgyz_first_names = [
    "Айбек", "Бакыт", "Дастан", "Эркин", "Талант", "Нурлан", "Бекзат", "Каныбек",
    "Айсулуу", "Гульназ", "Нуржан", "Кайыргүл", "Айпери", "Жанар", "Эльмира", "Мадина",
]
russian_first_names = [
    "Александр", "Дмитрий", "Максим", "Сергей", "Андрей", "Елена", "Ольга", "Анна",
]
uzbek_first_names = [
    "Азамат", "Бекзод", "Дилшод", "Шухрат", "Жахонгир", "Илхом", "Отабек", "Парвиз",
    "Мадина", "Гульнора", "Диёра", "Наргиза",
]

last_names = [
    "Караев", "Алиев", "Усенов", "Мамытов", "Ибраимов", "Садыков", "Жумабеков", "Искаков", "Турсунов", "Каримов",
]


similar_first_names = ["Айбек", "Азамат", "Нурлан", "Мадина", "Гульнора", "Бекзод"]
used_fio = set(
    f"{s.first_name.strip()} {s.last_name.strip()}".strip()
    for s in Student.objects.filter(company=company)
)


def pick_unique_name(pool, idx):
    for _ in range(300):
        first = random.choice(pool)
        last = random.choice(last_names)
        fio = f"{first} {last}"
        if fio not in used_fio:
            used_fio.add(fio)
            return first, last
    first = random.choice(pool)
    last = f"{random.choice(last_names)}-{idx}"
    fio = f"{first} {last}"
    used_fio.add(fio)
    return first, last

created_total = 0
for group in groups:
    target = random.randint(5, 10)
    existing = group.students.count()
    need = max(0, target - existing)
    if need == 0:
        print(f"[{group.id}] {group.name}: уже {existing}, пропуск")
        continue

    kg_count = round(need * 0.6)
    ru_count = round(need * 0.1)
    uz_count = need - kg_count - ru_count

    pools = ([kyrgyz_first_names] * kg_count) + ([russian_first_names] * ru_count) + ([uzbek_first_names] * uz_count)
    random.shuffle(pools)
    unique_target = round(need * 0.8)

    group_created = 0
    for idx, pool in enumerate(pools, start=1):
        effective_pool = pool if idx <= unique_target else similar_first_names
        first_name, last_name = pick_unique_name(effective_pool, idx)
        phone = f"+99670{random.randint(100000, 999999)}"
        student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            telegram="",
            company=company,
            company_name=company.name,
            can_login=True,
            primary_course=group.course,
            notes="",
        )
        group.students.add(student)
        group_created += 1
        created_total += 1

    print(f"[{group.id}] {group.name}: было {existing}, добавлено {group_created}, стало {group.students.count()} (цель {target})")

print("=" * 60)
print(f"Готово. Всего создано студентов: {created_total}")
