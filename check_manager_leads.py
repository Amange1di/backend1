import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, TrialLead

print("=== Проверка менеджеров ===")
managers = User.objects.filter(role=User.Role.MANAGER)
for m in managers:
    print(f"\nМенеджер: {m.username}")
    print(f"  Company: {m.company}")
    print(f"  Company name: {m.company_name}")
    print(f"  Role: {m.role}")

print("\n=== Проверка заявок (TrialLead) ===")
leads = TrialLead.objects.all()
for lead in leads:
    print(f"\nЗаявка: {lead.full_name}")
    print(f"  Phone: {lead.phone}")
    print(f"  Company: {lead.company}")
    print(f"  Company name: {lead.company_name}")
    print(f"  Source: {lead.source}")

print("\n=== Проверка компании 'Edu Center Pro' ===")
company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    print(f"Компания: {company.name}")
    print(f"  ID: {company.id}")
    leads_for_company = TrialLead.objects.filter(company=company)
    print(f"  Заявки для этой компании: {leads_for_company.count()}")
    for lead in leads_for_company:
        print(f"    - {lead.full_name}: {lead.phone}")