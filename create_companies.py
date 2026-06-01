from core.models import Company, CompanyBalance, User

# Удаляем существующие компании и балансы
Company.objects.all().delete()
CompanyBalance.objects.all().delete()

# Получаем супер-админа как владельца
owner = User.objects.filter(role=User.Role.ADMIN).first() or User.objects.filter(is_superuser=True).first()
print(f"Using owner: {owner.username}")

# Список компаний для создания
companies_data = [
    {"name": "Edu Center Pro", "slug": "edu-center-pro", "city": "bishkek", "category": "it"},
    {"name": "English School Osh", "slug": "english-school-osh", "city": "osh", "category": "languages"},
    {"name": "IT Academy Bishkek", "slug": "it-academy-bishkek", "city": "bishkek", "category": "it"},
    {"name": "Language Lab", "slug": "language-lab", "city": "bishkek", "category": "languages"},
    {"name": "Design Hub KG", "slug": "design-hub-kg", "city": "bishkek", "category": "design"},
    {"name": "Smart Kids Center", "slug": "smart-kids-center", "city": "osh", "category": "other"},
    {"name": "Code Masters", "slug": "code-masters", "city": "bishkek", "category": "it"},
    {"name": "International School", "slug": "international-school", "city": "bishkek", "category": "languages"},
]

created_count = 0
for data in companies_data:
    company = Company.objects.create(
        name=data["name"],
        slug=data["slug"],
        city=data["city"],
        category=data["category"],
        owner=owner,
    )
    CompanyBalance.objects.create(company=company, balance=1000)
    print(f"Created: {company.name}")
    created_count += 1

print(f"\nTotal companies: {Company.objects.count()}")
print(f"All created successfully!")