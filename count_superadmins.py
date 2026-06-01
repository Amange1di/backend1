import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User

super_admins = User.objects.filter(role='super_admin')
print(f'Количество супер-админов: {super_admins.count()}')
for user in super_admins:
    print(f'  - {user.username} ({user.email})')
