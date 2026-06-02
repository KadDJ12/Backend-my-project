from django.db import models
from Branches.models import Branch
from Students.models import Student

class Group(models.Model):
    name = models.CharField(max_length=255)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='groups')
    students = models.ManyToManyField(Student, through='GroupMembership', related_name='groups')

    def __str__(self):
        return f"{self.name} - {self.status}"


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='memberships')
    join_date = models.DateField(auto_now_add=True)
    leave_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('group', 'student')

    def __str__(self):
        return f"{self.student} in {self.group} (Joined: {self.join_date})"
