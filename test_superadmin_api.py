import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from core.views import SuperAdminStatsView
from core.models import User

# Создаем тестового админа
admin, created = User.objects.get_or_create(
    username='test_admin',
    defaults={'role': User.Role.ADMIN, 'is_staff': True}
)
if created:
    admin.set_password('testpass')
    admin.save()

# Создаем тестовый запрос
factory = RequestFactory()
request = factory.get('/api/super-admin/stats/')
request.user = admin

view = SuperAdminStatsView.as_view()
response = view(request)

print(f'Status: {response.status_code}')
print(f'Data keys: {list(response.data.keys())}')

if response.status_code == 200:
    print('\n=== Summary ===')
    summary = response.data.get('summary', {})
    for key, value in summary.items():
        print(f'{key}: {value}')
    
    print('\n=== Companies ===')
    companies = response.data.get('companies', [])
    print(f'Total companies: {len(companies)}')
    if companies:
        for company in companies[:3]:
            print(f"  - {company.get('name')}: {company.get('students_count')} студентов, баланс: {company.get('balance')} eC")
