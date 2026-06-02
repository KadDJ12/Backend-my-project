from django.db import models
from Branches.models import Branch, Subject
from Students.models import Student

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('group', 'Group'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='individual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='subscription_plans')
    
    subjects = models.ManyToManyField(Subject, related_name='subscription_plans')

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.branch.name}"


class PlanPriceTier(models.Model):  
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='price_tiers')
    price_per_lesson = models.IntegerField() 
    lessons_per_month = models.IntegerField()

    class Meta:
        unique_together = ('subscription_plan', 'lessons_per_month')
        ordering = ['lessons_per_month']

    def __str__(self):
        return f"{self.subscription_plan.name} | {self.lessons_per_month} занять по {self.price_per_lesson} $"


class StudentSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='subscriptions')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='student_subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='student_subscriptions')
    start_date = models.DateField()

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.subscription_plan.name} ({self.subject.name})"