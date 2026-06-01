import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import User, Company, CompanyBalance

print('=== Users by role ===')
for role in User.Role:
    count = User.objects.filter(role=role).count()
    print(f'{role.name}: {count}')

print('\n=== Companies ===')
print(f'Total: {Company.objects.count()}')
for c in Company.objects.all()[:3]:
    bal = CompanyBalance.objects.filter(company=c).first()
    print(f'  {c.name}: {c.students.count()} студентов, баланс: {bal.balance if bal else 0} eC')