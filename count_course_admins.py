import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User

course_admins = User.objects.filter(role='course_admin')
print(f'Количество course_admin: {course_admins.count()}')
for user in course_admins:
    print(f'  - {user.username} (has_password: {user.has_usable_password()})')
