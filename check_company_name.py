import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Student, User, Company

company = Company.objects.filter(slug='smart-kids-center').first()
students = Student.objects.filter(company=company)

print('Всего студентов:', students.count())
print('С company_name:', Student.objects.filter(company=company, company_name__isnull=False, company_name__gt='').count())
print('Без company_name:', Student.objects.filter(company=company).exclude(company_name__isnull=False, company_name__gt='').count())

mgr = User.objects.filter(username='manager_smartkids_1').first()
if mgr:
    print('company_name менеджера:', repr(mgr.company_name))
    print('company менеджера:', repr(str(mgr.company) if mgr.company else None))
else:
    print('Менеджер не найден')
