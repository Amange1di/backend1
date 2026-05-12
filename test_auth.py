import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import User

user = authenticate(username='1', password='11')
if user:
    print(f'User: {user.username}')
    print(f'Role: {user.role}')
    print(f'Superuser: {user.is_superuser}')
    print(f'Email: {user.email}')
else:
    print('Invalid credentials')
