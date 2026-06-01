import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

BASE_URL = 'http://localhost:8000/api'

# Логин как менеджер
response = requests.post(f'{BASE_URL}/auth/login/', json={
    'username': 'manager_smartkids_1',
    'password': 'admin123'
})

if response.status_code != 200:
    print(f"❌ Логин не удался: {response.status_code}")
    print(response.text)
    exit(1)

token = response.json().get('token')
print(f"✅ Логин успешен: {token[:20]}...")

headers = {'Authorization': f'Token {token}'}

# Проверка курсов
print("\n=== Курсы ===")
response = requests.get(f'{BASE_URL}/courses/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    courses = data if isinstance(data, list) else data.get('results', [])
    print(f"Курсов: {len(courses)}")
    for course in courses:
        print(f"  - {course.get('title')}")
else:
    print(f"Ошибка: {response.text}")

# Проверка студентов
print("\n=== Студенты ===")
response = requests.get(f'{BASE_URL}/students/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    students = data if isinstance(data, list) else data.get('results', [])
    print(f"Студентов: {len(students)}")
else:
    print(f"Ошибка: {response.text}")

# Проверка учителей
print("\n=== Учителя ===")
response = requests.get(f'{BASE_URL}/teachers/', headers=headers)
print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    teachers = data if isinstance(data, list) else data.get('results', [])
    print(f"Учителей: {len(teachers)}")
    for teacher in teachers[:5]:
        print(f"  - {teacher.get('first_name')} {teacher.get('last_name')}")
else:
    print(f"Ошибка: {response.text}")
