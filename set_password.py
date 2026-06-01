import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User

# Установить пароль для менеджера
username = input("Введите логин пользователя: ")
password = input("Введите новый пароль: ")

try:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"✅ Пароль установлен для пользователя: {username}")
except User.DoesNotExist:
    print(f"❌ Пользователь {username} не найден!")
