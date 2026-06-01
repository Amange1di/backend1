import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Company, Student, CompanyBalance

# Количество компаний
companies = Company.objects.all()
companies_count = companies.count()

# Количество студентов
students = Student.objects.all()
students_count = students.count()

# Полная сумма баланса всех компаний
total_balance = 0
balances = CompanyBalance.objects.all()
for balance in balances:
    total_balance += balance.balance

print(f'Количество компаний: {companies_count}')
print(f'Количество студентов: {students_count}')
print(f'Полная сумма баланса (eduCoins): {total_balance}')
