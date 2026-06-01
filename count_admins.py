import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User

admins = User.objects.filter(role='admin')
print(f'Количество админов: {admins.count()}')
for user in admins:
    print(f'  - {user.username} ({user.email})')
