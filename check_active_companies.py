import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Company

active = Company.objects.filter(is_active=True)
inactive = Company.objects.filter(is_active=False)

print(f'Активные компании: {active.count()}')
for c in active:
    print(f'  - {c.name} (owner: {c.owner.username if c.owner else "None"})')

print(f'\nНеактивные компании: {inactive.count()}')
for c in inactive:
    print(f'  - {c.name} (owner: {c.owner.username if c.owner else "None"})')
