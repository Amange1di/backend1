import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import User

print('Total users:', User.objects.count())
for u in User.objects.all()[:10]:
    print(f'{u.id}: {u.username} - {u.role} - active={u.is_active}')
