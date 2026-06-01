import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company

print("Проверка course_admin и компаний:")
for admin in User.objects.filter(role=User.Role.COURSE_ADMIN).order_by('id'):
    company = Company.objects.filter(name=admin.company_name).first()
    if company:
        print(f"  {admin.username} -> {admin.company_name} (Company ID: {company.id}, owner: {company.owner.username})")
    else:
        print(f"  {admin.username} -> {admin.company_name} (Компания НЕ НАЙДЕНА)")
