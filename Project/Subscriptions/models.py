from django.db import models
from Branches.models import Branch
from Students.models import Student



class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='MONTHLY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='subscription_plans')
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class PlanPriceTier(models.Model):  
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='price_tiers')
    price_per_lesson = models.IntegerField()
    lessons_per_month = models.IntegerField()
    class Meta:
        unique_together = ('subscription_plan', 'lessons_per_month')
    def __str__(self):
        return f"{self.subscription_plan.name} | {self.lessons_per_month} lessons @ {self.price_per_lesson} each"


class StudentSubscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='subscriptions')
    plan_tier = models.ForeignKey(PlanPriceTier, on_delete=models.PROTECT, related_name='student_subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    def __str__(self):
        plan_name = self.plan_tier.subscription_plan.name
        return f"{self.student.user.username} - {plan_name} (End: {self.end_date})"