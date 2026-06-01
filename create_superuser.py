from core.models import User
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
print('Superuser created: admin / admin123')
