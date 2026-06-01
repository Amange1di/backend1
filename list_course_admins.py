import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User

print("Все course_admin:")
for admin in User.objects.filter(role=User.Role.COURSE_ADMIN).order_by('id'):
    print(f"  id={admin.id}, username={admin.username}, company_name={admin.company_name}, email={admin.email}")
