from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255,unique=True)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')



    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=255)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='subject')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'name'],
                name='unique_subject_name_per_branch',
            )
        ]


