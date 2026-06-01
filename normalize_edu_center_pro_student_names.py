import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from core.models import Company, Student

company = Company.objects.filter(name='Edu Center Pro').first()
if not company:
    raise SystemExit("Компания 'Edu Center Pro' не найдена")

students = list(Student.objects.filter(company=company).order_by('id'))
if not students:
    raise SystemExit('Студенты не найдены')

n = len(students)
unique_target = int(round(n * 0.8))

# 80%: максимально разнообразные имена
unique_first_pool = [
    'Айзада','Айпери','Айнура','Айжан','Алина','Амина','Бегайым','Гульзат','Гульмира','Динара','Жанара','Камила','Мээрим','Назгуль','Нуриза','Перизат','Сезим','Толкунай','Чолпон','Элина',
    'Айбек','Арстан','Бекболот','Бакыт','Данияр','Жоомарт','Кайрат','Кубаныч','Мирлан','Нурсултан','Тилек','Улан','Эрмек','Азамат','Элдар','Темирлан','Руслан','Ильяс','Самат','Адилет',
    'Александр','Дмитрий','Сергей','Андрей','Елена','Ольга','Анна','Мария','Ирина','Наталья',
    'Бекзод','Дилшод','Шухрат','Жахонгир','Илхом','Отабек','Гульнора','Наргиза','Диёра','Мухаммад'
]

last_pool = [
    'Караев','Алиев','Усенов','Мамытов','Ибраимов','Садыков','Жумабеков','Искаков','Турсунов','Каримов',
    'Абдылдаев','Кудайбердиев','Токтогулов','Матраимов','Нуров','Саидов','Усмонов','Алимов','Рахимов','Якубов',
    'Иванов','Петров','Смирнов','Волков','Козлов','Сидоров','Новиков','Федоров','Морозов','Алексеев'
]

# 20%: похожие имена (повторы), но ФИО всё равно уникальные
similar_first_pool = ['Айбек', 'Азамат', 'Нурлан', 'Мадина', 'Гульнора', 'Бекзод']

used_fio = set()
used_usernames = set(s.user.username for s in students if s.user and s.user.username)


def make_unique_fio(first_choices, idx):
    for _ in range(500):
        first = random.choice(first_choices)
        last = random.choice(last_pool)
        fio = f"{first} {last}"
        if fio not in used_fio:
            used_fio.add(fio)
            return first, last
    # fallback: гарантированная уникальность
    first = random.choice(first_choices)
    last = f"{random.choice(last_pool)}-{idx}"
    fio = f"{first} {last}"
    used_fio.add(fio)
    return first, last


def slug(s: str):
    return ''.join(ch.lower() for ch in s if ch.isalpha())


for i, st in enumerate(students, start=1):
    pool = unique_first_pool if i <= unique_target else similar_first_pool
    first, last = make_unique_fio(pool, i)

    st.first_name = first
    st.last_name = last
    st.save(update_fields=['first_name', 'last_name'])

    if st.user:
        st.user.first_name = first
        st.user.last_name = last
        # при наличии user обновляем username/email в уникальный формат
        base = f"{slug(first)}.{slug(last)}"
        candidate = f"{base}@edupro.kg"
        k = 1
        while candidate in used_usernames:
            k += 1
            candidate = f"{base}{k}@edupro.kg"
        used_usernames.add(candidate)
        st.user.username = candidate
        st.user.email = candidate
        st.user.save(update_fields=['first_name', 'last_name', 'username', 'email'])

print(f"Обновлено студентов: {n}")
print(f"Уникальных по схеме ~80%: {unique_target}")
print(f"Похожих по схеме ~20%: {n - unique_target}")
