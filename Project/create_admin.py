import os
import django

# Вказуємо шлях до налаштувань твого проєкту
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username_field = User.USERNAME_FIELD  # Динамічно визначає, як називається твоє поле (phone чи phone_number)

admin_login = '0984097270'
admin_password = '12345'

try:
    # Перевіряємо, чи є вже такий користувач, щоб не створювати його двічі при кожному запуску
    if not User.objects.filter(**{username_field: admin_login}).exists():
        User.objects.create_superuser(**{username_field: admin_login, 'password': admin_password})
        print(f"✅ Суперкористувач {admin_login} успішно створений!")
    else:
        print(f"ℹ️ Суперкористувач {admin_login} вже існує. Пропускаємо.")
except Exception as e:
    print(f"❌ Помилка створення суперкористувача: {e}")