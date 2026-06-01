from core.models import Company, User

# Создаем супер-админа
try:
    admin = User.objects.get(username='admin')
except User.DoesNotExist:
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Created superuser: admin / admin123")

# Удаляем старые компании
Company.objects.all().delete()
print("Deleted all companies")

# Список компаний
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

for data in companies_data:
    company = Company.objects.create(
        name=data["name"],
        slug=data["slug"],
        city=data["city"],
        category=data["category"],
        owner=admin,
    )
    print(f"✓ Created: {company.name}")

print(f"\n✅ Total: {Company.objects.count()} companies created")