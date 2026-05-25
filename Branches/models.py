from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, )
    STARUS_CHOICES = [
        ('ACTIVE', 'active'),
        ('CLOSED', 'closed'),
    ]
    status = models.CharField(max_length=10, choices=STARUS_CHOICES, default='ACTIVE')



    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=255)
    STARUS_CHOICES = [
        ('ACTIVE', 'active'),
        ('CLOSED', 'closed'),
    ]
    status = models.CharField(max_length=10, choices=STARUS_CHOICES, default='ACTIVE')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='subject')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'name'],
                name='unique_subject_name_per_branch',
            )
        ]


