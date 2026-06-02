from django.db import models, transaction
from django.conf import settings
from django.db.models import Q
from Branches.models import Branch, Subject
from Students.models import Student
from Groups.models import Group
from django.core.exceptions import ValidationError
import datetime


class Lesson(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    title = models.CharField(max_length=255)

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='lessons')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='lessons')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='lessons')

    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='individual_lessons')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='group_lessons')

    def clean(self):
        super().clean()

        if self.student and self.group:
            raise ValidationError('A lesson cannot be assigned to both a student and a group.')
        if not self.student and not self.group:
            raise ValidationError('A lesson must be assigned to either a student or a group.')

        if hasattr(self, 'teacher') and self.teacher and self.teacher.role != 'teacher':
            raise ValidationError('Assigned teacher must have the TEACHER role.')

        # Check if branch or subject is archived (only for new lessons)
        if not self.pk:
            if hasattr(self, 'subject') and self.subject and self.subject.status == 'archived':
                raise ValidationError('Cannot create a lesson with an archived subject.')
            if hasattr(self, 'branch') and self.branch and self.branch.status == 'archived':
                raise ValidationError('Cannot create a lesson in an archived branch.')
            if self.group and self.group.status == 'archived':
                raise ValidationError('Cannot create a lesson with an archived group.')

        if self.date and self.start_time and self.end_time:
            overlapping_lessons = Lesson.objects.filter(
                date=self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk).exclude(status='CANCELLED')

            if overlapping_lessons.filter(teacher=self.teacher).exists():
                raise ValidationError('This teacher already has a lesson scheduled at this time.')

            if self.student:
                student_conflicts = overlapping_lessons.filter(
                    Q(student=self.student) | Q(group__students=self.student, group__memberships__leave_date__isnull=True)
                ).exists()
                if student_conflicts:
                    raise ValidationError('This lesson overlaps with another scheduled lesson for the assigned student.')

            if self.group and self.group.pk:
                # Only check students currently in the group
                group_students = self.group.students.filter(memberships__leave_date__isnull=True, memberships__group=self.group)
                group_conflict = overlapping_lessons.filter(
                    Q(student__in=group_students) | Q(group__students__in=group_students, group__memberships__leave_date__isnull=True)
                ).distinct().exists()
                if group_conflict:
                    raise ValidationError({'group': 'Один або більше студентів з цієї групи мають інший урок у цей час.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.date} {self.start_time}-{self.end_time}"


class Attendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('lesson', 'student')

    def clean(self):
        super().clean()

        if self.lesson.status == 'CANCELLED':
            raise ValidationError('Cannot mark attendance for a cancelled lesson.')

        is_participant = False

        if self.lesson.student and self.lesson.student == self.student:
            is_participant = True
        elif self.lesson.group and self.lesson.group.students.filter(pk=self.student.pk, memberships__leave_date__isnull=True).exists():
            is_participant = True

        if not is_participant:
            raise ValidationError('Цього студента немає в списках на цей урок.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Присутній" if self.present else "Відсутній"
        return f"{self.student} - {self.lesson.date} ({status})"


class LessonTemplate(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='lesson_templates')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='lesson_templates')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='lesson_templates')
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='lesson_templates')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='lesson_templates')
    
    days_of_week = models.JSONField() # Array of integers: [0, 2] for Monday, Wednesday
    start_time = models.TimeField()
    end_time = models.TimeField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.student and self.group:
            raise ValidationError('A template cannot have both a student and a group.')
        if not self.student and not self.group:
            raise ValidationError('A template must have either a student or a group.')
        if self.start_date > self.end_date:
            raise ValidationError('Start date must be before end date.')
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time.')
        if not isinstance(self.days_of_week, list) or not all(isinstance(d, int) and 0 <= d <= 6 for d in self.days_of_week):
            raise ValidationError('Days of week must be a list of integers from 0 (Monday) to 6 (Sunday).')
            
        if self.subject and self.subject.status == 'archived':
            raise ValidationError('Cannot create a template with an archived subject.')
        if self.branch and self.branch.status == 'archived':
            raise ValidationError('Cannot create a template in an archived branch.')
        if self.group and self.group.status == 'archived':
            raise ValidationError('Cannot create a template with an archived group.')

    def generate_lessons(self, strategy='block'):
        """
        Generates individual lessons based on the template.
        strategy: 'block' (fail everything on any conflict) or 'skip' (create conflict-free, list skipped ones)
        """
        created_lessons = []
        conflicts = []
        
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() in self.days_of_week:
                lesson = Lesson(
                    branch=self.branch,
                    teacher=self.teacher,
                    subject=self.subject,
                    student=self.student,
                    group=self.group,
                    date=current_date,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    title=f"{self.subject.name} - Recurring",
                    status='SCHEDULED'
                )
                try:
                    lesson.clean()
                    created_lessons.append(lesson)
                except ValidationError as e:
                    conflicts.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'error': e.message_dict if hasattr(e, 'message_dict') else str(e)
                    })
            current_date += datetime.timedelta(days=1)

        if conflicts and strategy == 'block':
            raise ValidationError({
                'message': 'Conflicts detected for some planned dates. Creation blocked.',
                'conflicts': conflicts
            })

        # Save generated lessons
        with transaction.atomic():
            for lesson in created_lessons:
                lesson.save()

        return created_lessons, conflicts