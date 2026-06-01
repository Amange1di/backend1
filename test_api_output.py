import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

BASE_URL = 'http://localhost:8000/api/'

# Логин как менеджер
response = requests.post(f'{BASE_URL}auth/login/', json={
    'username': 'manager_smartkids_1',
    'password': 'admin123'
})

if response.status_code != 200:
    print(f"❌ Логин не удался: {response.status_code}")
    print(response.text[:200])
    exit(1)

token = response.json().get('token')
print(f"✅ Логин успешен")

headers = {'Authorization': f'Token {token}'}

# Проверка курсов
print("\n=== Курсы ===")
response = requests.get(f'{BASE_URL}courses/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    courses = data if isinstance(data, list) else data.get('results', [])
    print(f"Курсов найдено: {len(courses)}")
    for course in courses:
        print(f"  ✓ {course.get('title')}")
else:
    print(f"❌ Ошибка: {response.text[:200]}")

# Проверка студентов
print("\n=== Студенты ===")
response = requests.get(f'{BASE_URL}students/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    students = data if isinstance(data, list) else data.get('results', [])
    print(f"Студентов найдено: {len(students)}")
else:
    print(f"❌ Ошибка: {response.text[:200]}")

# Проверка учителей
print("\n=== Учителя ===")
response = requests.get(f'{BASE_URL}teachers/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    teachers = data if isinstance(data, list) else data.get('results', [])
    print(f"Учителей найдено: {len(teachers)}")
    for teacher in teachers[:5]:
        print(f"  ✓ {teacher.get('first_name')} {teacher.get('last_name')}")
else:
    print(f"❌ Ошибка: {response.text[:200]}")

# Проверка менеджеров
print("\n=== Менеджеры ===")
response = requests.get(f'{BASE_URL}managers/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    managers = data if isinstance(data, list) else data.get('results', [])
    print(f"Менеджеров найдено: {len(managers)}")
else:
    print(f"❌ Ошибка: {response.text[:200]}")

print("\n" + "="*50)
if len(courses) > 0 and len(students) > 0 and len(teachers) > 0:
    print("✅ ВСЕ ДАННЫЕ ОТОБРАЖАЮТСЯ!")
else:
    print("❌ ДАННЫЕ НЕ ОТОБРАЖАЮТСЯ - нужен перезапуск сервера")