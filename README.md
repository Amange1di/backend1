# EdUOsh CRM - Backend API

Django REST Framework backend для системы управления образовательным центром EdUOsh. Обеспечивает REST API для управления курсами, преподавателями, студентами, группами, расписанием и аудиториями.

## Технологический стек

- **Django**: 5.1+
- **Django REST Framework**: 3.16+
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **CORS**: django-cors-headers
- **Authentication**: Token-based

## Установка и настройка

### Требования

- Python 3.10+
- pip или poetry

### Шаг 1: Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### Шаг 2: Создание и применение миграций

```bash
python manage.py migrate
```

### Шаг 3: Создание суперпользователя (Admin)

```bash
python manage.py createsuperuser
```

Следуйте инструкциям в консоли для создания администратора.

### Шаг 4: Запуск сервера

```bash
python manage.py runserver
```

Сервер будет запущен на `http://localhost:8000`

## Структура проекта

```
backend/
├── config/              # Конфигурация Django проекта
│   ├── settings.py     # Основные настройки
│   ├── urls.py         # URL маршруты
│   ├── asgi.py         # ASGI конфигурация
│   └── wsgi.py         # WSGI конфигурация
├── core/               # Основное приложение
│   ├── models.py       # ORM модели данных
│   ├── views.py        # API views
│   ├── serializers.py  # Сериализаторы
│   ├── permissions.py  # Кастомные permissions
│   ├── urls.py         # URL маршруты core
│   ├── admin.py        # Django Admin конфигурация
│   ├── tests.py        # Unit тесты
│   └── migrations/     # Миграции БД
├── locale/             # Переводы (i18n)
│   ├── ky/             # Кыргызский
│   └── ru/             # Русский
├── db.sqlite3          # SQLite база (development)
├── manage.py           # Django CLI
└── requirements.txt    # Python зависимости
```

## Основные модели данных

### User (Пользователь)

Расширенная модель Django User с ролями:

- **admin** - Администратор системы
- **course_admin** - Администратор курса / Компания
- **manager** - Менеджер
- **teacher** - Преподаватель
- **student** - Студент

Поля: `username`, `email`, `first_name`, `last_name`, `phone`, `address`, `telegram`, `company_name`, `role`

### Course (Курс)

Описание курса обучения.

- Название, цена, длительность в неделях, продолжительность урока
- Описание, расписание, администраторы курса

### Student (Студент)

Информация о студенте.

- ФИ, телефон, telegram, компания
- Первичный курс, заметки

### Group (Группа)

Учебная группа.

- Название, курс, преподаватель
- Расписание (дни недели, время), аудитория
- Количество уроков, даты начала и окончания

### Auditorium (Аудитория)

Помещение для занятий.

- Название, номер, компания

### Attendance (Посещаемость)

Запись о посещаемости студента на занятии.

- Студент, группа, дата урока, статус присутствия

### Payment (Платежи)

История платежей студентов.

- Студент, сумма, дата платежа, описание

## API Endpoints

### Аутентификация

- `POST /api/auth/login/` - Вход в систему
- `POST /api/auth/logout/` - Выход из системы
- `GET /api/auth/me/` - Получить текущего пользователя

### Пользователи

- `GET /api/users/` - Список всех пользователей
- `POST /api/users/` - Создать пользователя
- `GET /api/users/{id}/` - Детали пользователя
- `PUT /api/users/{id}/` - Обновить пользователя
- `DELETE /api/users/{id}/` - Удалить пользователя

### Курсы

- `GET /api/courses/` - Список курсов
- `POST /api/courses/` - Создать курс
- `GET /api/courses/{id}/` - Детали курса
- `PUT /api/courses/{id}/` - Обновить курс
- `DELETE /api/courses/{id}/` - Удалить курс

### Студенты

- `GET /api/students/` - Список студентов
- `POST /api/students/` - Создать студента
- `GET /api/students/{id}/` - Детали студента
- `PUT /api/students/{id}/` - Обновить студента
- `DELETE /api/students/{id}/` - Удалить студента

### Группы

- `GET /api/groups/` - Список групп
- `POST /api/groups/` - Создать группу
- `GET /api/groups/{id}/` - Детали группы
- `PUT /api/groups/{id}/` - Обновить группу
- `DELETE /api/groups/{id}/` - Удалить группу

### Аудитории

- `GET /api/auditoriums/` - Список аудиторий
- `POST /api/auditoriums/` - Создать аудиторию
- `GET /api/auditoriums/{id}/` - Детали аудитории
- `PUT /api/auditoriums/{id}/` - Обновить аудиторию
- `DELETE /api/auditoriums/{id}/` - Удалить аудиторию

### Посещаемость

- `GET /api/attendance/` - История посещаемости
- `POST /api/attendance/` - Создать запись посещаемости
- `PUT /api/attendance/{id}/` - Обновить запись

### Платежи

- `GET /api/payments/` - История платежей
- `POST /api/payments/` - Создать платеж
- `GET /api/payments/{id}/` - Детали платежа

## Аутентификация

API использует Token-based аутентификацию:

1. Получить токен:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

2. Использовать токен в заголовках:

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/users/
```

## Permissions (Права доступа)

- **Admin**: Полный доступ ко всем ресурсам
- **Course Admin**: Управление своими курсами и связанными группами
- **Teacher**: Просмотр и управление своими группами
- **Manager**: Ограниченный доступ к просмотру данных
- **Student**: Просмотр только своих данных

## Управление данными из Django Admin

Откройте Django Admin панель:

```
http://localhost:8000/admin
```

## Документация API (Swagger/OpenAPI)

Интерактивная документация доступна в:

```
http://localhost:8000/api/schema/swagger-ui/
```

## Миграции базы данных

### Создать новую миграцию после изменения модели:

```bash
python manage.py makemigrations
```

### Применить миграции:

```bash
python manage.py migrate
```

### Просмотреть SQL миграции:

```bash
python manage.py sqlmigrate core 0001
```

## Переводы (Локализация)

Поддерживаемые языки: Русский (ru), Кыргызский (ky)

Добавить перевод:

```bash
python manage.py makemessages -l ky
# Отредактировать файлы в locale/ky/LC_MESSAGES/django.po
python manage.py compilemessages
```

## Переменные окружения

Создать файл `.env` в папке backend:

```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## Режимы работы

### Development

```bash
python manage.py runserver
```

### Production (с Gunicorn)

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Тестирование

Запуск тестов:

```bash
python manage.py test
```

Запуск тестов с покрытием:

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Debugging

### Django Debug Toolbar

1. Установить: `pip install django-debug-toolbar`
2. Добавить в INSTALLED_APPS в settings.py
3. Обновить urls.py
4. Откройте http://localhost:8000 с браузера

### Django Shell

```bash
python manage.py shell
>>> from core.models import User
>>> User.objects.all()
```

## Проблемы и решения

### Ошибка подключения к БД

- Проверьте наличие папки с БД: `ls backend/db.sqlite3`
- Пересоздайте БД: `rm db.sqlite3` и `python manage.py migrate`

### CORS ошибки

- Проверьте CORS_ALLOWED_ORIGINS в settings.py
- Убедитесь, что frontend запущен на правильном порту

### SuperUser не создается

```bash
python manage.py flush  # Сбросить БД
python manage.py migrate
python manage.py createsuperuser
```

## Полезные ссылки

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)

## Лицензия

Proprietary - EdUOsh CRM System

## Автор

EdUOsh Development Team
