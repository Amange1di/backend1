import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

# Удаляем если есть
User.objects.filter(username='superadmin').delete()

# Создаем супер-админа
super_admin = User.objects.create_superuser(
    username='superadmin',
    email='superadmin@edu.kg',
    password='super123',
    role=User.Role.SUPER_ADMIN,
    first_name='Super',
    last_name='Admin'
)

print(f'Супер-админ создан:')
print(f'  Логин: {super_admin.username}')
print(f'  Пароль: super123')
print(f'  Email: {super_admin.email}')
print(f'  Роль: {super_admin.get_role_display()}')
