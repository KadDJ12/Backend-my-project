from django.db import models
from Branches.models import Branch

class Student(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=22, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255)
    
    # Parent/guardian contact info
    parent_name = models.CharField(max_length=255, null=True, blank=True)
    parent_phone = models.CharField(max_length=22, null=True, blank=True)
    parent_email = models.EmailField(null=True, blank=True)
    parent_relationship = models.CharField(max_length=100, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='students')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone}) - {self.status}"



