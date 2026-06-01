from core.models import Company, User

# Создаем супер-админа
try:
    admin = User.objects.get(username='admin')
except User.DoesNotExist:
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Created superuser: admin / admin123")

# Получаем все компании
companies = list(Company.objects.all())
print(f"Found {len(companies)} companies")

# Создаем course_admin для каждой компании
created_count = 0
for company in companies:
    username = f"admin_{company.slug}"
    
    # Проверяем, существует ли уже админ для этой компании
    if User.objects.filter(username=username).exists():
        print(f"✓ Already exists: {username} for {company.name}")
        continue
    
    # Создаем нового course_admin
    user = User.objects.create_user(
        username=username,
        password="admin123",
        first_name=f"{company.name.split()[0]} Admin",
        phone=f"+996 700 00 00 {created_count:02d}",
        address="Bishkek",
        role=User.Role.COURSE_ADMIN,
        company=company,
        max_managers=3,
        max_pages=1,
        max_blocks=7,
    )
    print(f"✓ Created: {username} for {company.name}")
    created_count += 1

print(f"\n✅ Total course admins created: {created_count}")
print(f"Total companies: {Company.objects.count()}")
print(f"Total course admins: {User.objects.filter(role=User.Role.COURSE_ADMIN).count()}")
