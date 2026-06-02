from django.db import models
from django.conf import settings
from django.db.models import Q                          # FIX 3: explicit Q import
from Branches.models import Branch, Subject
from Students.models import Student
from Groups.models import Group
from django.core.exceptions import ValidationError


class Lesson(models.Model):
    STATUS_CHOICES = [                                  # FIX typo: STARUS → STATUS
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
    groups = models.ManyToManyField(Group, blank=True, related_name='group_lessons')
    def clean(self):
        super().clean()

        has_groups = self.pk and self.groups.exists()

        if self.student and has_groups:
            raise ValidationError('A lesson cannot be assigned to both a student and a group.')
        if not self.student and not has_groups:
            raise ValidationError('A lesson must be assigned to either a student or a group.')

        if hasattr(self, 'teacher') and self.teacher and self.teacher.role != 'teacher':
            raise ValidationError('Assigned teacher must have the TEACHER role.')

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
                    Q(student=self.student) | Q(groups__students=self.student)
                ).exists()
                if student_conflicts:
                    raise ValidationError('This lesson overlaps with another lesson for this student.')

            if has_groups:
                group_students = Student.objects.filter(
                    group_memberships__in=self.groups.all()
                )
                group_conflict = overlapping_lessons.filter(
                    Q(student__in=group_students) | Q(groups__students__in=group_students)
                ).distinct().exists()
                if group_conflict:
                    raise ValidationError({
                        'groups': 'Один або більше студентів з цієї групи мають інший урок у цей час.'
                    })
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
        elif self.lesson.group and self.lesson.group.students.filter(pk=self.student.pk).exists():
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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='individual_templates')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='group_templates')
    days_of_week = models.JSONField(help_text="Список ID днів тижня (0 для Понеділка, 6 для Неділі)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)


    def clean(self):
        super().clean()

        if self.student and self.group:
            raise ValidationError('Шаблон не може бути призначений одночасно студенту і групі.')
        if not self.student and not self.group:
            raise ValidationError('Шаблон має бути призначений або студенту, або групі.')

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Дата початку періоду дії не може бути більшою за дату закінчення.')

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Час початку уроку повинен бути меншим за час його завершення.')

        if not isinstance(self.days_of_week, list) or len(self.days_of_week) == 0:
            raise ValidationError('Необхідно вказати хоча б один день тижня у вигляді списку чисел.')
            
        for day in self.days_of_week:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValidationError('ID дня тижня має бути цілим числом від 0 (Понеділок) до 6 (Неділя).')


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def __str__(self):
        type_name = f"Група {self.group.name}" if self.group else f"Студент {self.student.first_name}"
        return f"Шаблон: {self.subject.name} для {type_name} ({self.start_date} - {self.end_date})"