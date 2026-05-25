from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

# перевизначення перевірки кастомного користувача для використання телефону
# замість імені користувача.
class PhoneBackend(ModelBackend):
    def authenticate(self, request, phone=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(phone=phone)
        except UserModel.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
    