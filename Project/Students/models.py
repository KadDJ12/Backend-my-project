from django.db import models
from Branches.models import Branch

class Student(models.Model):
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=22, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    home_address = models.CharField()
    parent_nuber = models.CharField(max_length=22)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('dropped', 'Dropped'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='students')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone}) - {self.status}"



