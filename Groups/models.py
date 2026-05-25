from django.db import models
from Branches.models import Branch
from Students.models import Student

class Group(models.Model):
    name = models.CharField()
    STARUS_CHOICES = [
        ('ACTIVE', 'active'),
        ('CLOSED', 'closed'),
    ]

    status = models.CharField(max_length=10, choices=STARUS_CHOICES, default='ACTIVE')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='group')
    students = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='group')

    def __str__(self):
        return f"{self.name} - {self.status}"
