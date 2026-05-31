from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from Branches.models import Branch


class CustomUserManager(BaseUserManager):
    def create_user(self,phone, password= None, **extra_fields):
        if not phone:
            raise ValueError('The Phone number must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, phone, password= None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(phone, password, **extra_fields)



class CustomUser(AbstractUser):
    username = None
    phone = models.CharField(max_length=22, unique=True)
    role = models.CharField(
        max_length=10,
        choices=[('admin', 'Administrator'), ('teacher', 'Teacher'),],
        default='teacher',
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    branches = models.ManyToManyField(Branch, blank=True, related_name='branch')
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            self.is_staff = True


    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone}) - {self.role}"
