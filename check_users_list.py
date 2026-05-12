import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

users = User.objects.all()
print(f'Всего пользователей: {users.count()}')
for u in users:
    print(f'  {u.username} | {u.email} | {u.role} | superuser={u.is_superuser}')
