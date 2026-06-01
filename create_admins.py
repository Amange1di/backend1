import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

# Создаем супер-админа
superadmin_data = {
    'username': 'admin',
    'email': 'admin@example.com',
    'role': User.Role.SUPER_ADMIN,
    'first_name': 'Super',
    'last_name': 'Admin',
}

superadmin, created = User.objects.get_or_create(
    username=superadmin_data['username'],
    defaults=superadmin_data
)

if created:
    superadmin.set_password('admin123')
    superadmin.save()
    print("✅ Супер-админ создан:")
    print(f"  Логин: {superadmin.username}")
    print(f"  Пароль: admin123")
else:
    print("ℹ️ Супер-админ уже существует")
    print(f"  Логин: {superadmin.username}")
    print(f"  Пароль: admin123")

print()

# Создаем админа
admin_data = {
    'username': 'site_admin',
    'email': 'siteadmin@example.com',
    'role': User.Role.ADMIN,
    'first_name': 'Site',
    'last_name': 'Admin',
}

admin, created = User.objects.get_or_create(
    username=admin_data['username'],
    defaults=admin_data
)

if created:
    admin.set_password('admin123')
    admin.save()
    print("✅ Админ создан:")
    print(f"  Логин: {admin.username}")
    print(f"  Пароль: admin123")
else:
    print("ℹ️ Админ уже существует")
    print(f"  Логин: {admin.username}")
    print(f"  Пароль: admin123")
