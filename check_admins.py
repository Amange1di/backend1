from core.models import User

print("Admins:", User.objects.filter(role='ADMIN').count())
print("Superadmins:", User.objects.filter(role='SUPER_ADMIN').count())
print("All users:", User.objects.count())
for u in User.objects.all()[:5]:
    print(f"  - {u.username} ({u.role})")
