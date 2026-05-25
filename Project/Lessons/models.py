from django.db import models
from django.conf import settings
from Branches.models import Branch, Subject
from Students.models import Student
from Groups.models import Group
from django.core.exceptions import ValidationError


class Lesson(models.Model):
    STARUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STARUS_CHOICES, default='SCHEDULED')
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
                                                        # перевірка чи ми не додаємо учня з роллю вчитель
        if hasattr(self, 'teacher') and self.teacher and self.teacher.role != 'teacher':
            raise ValidationError('Assigned teacher must have the TEACHER role.')
            
        
        if self.date and self.start_time and self.end_time:
            overlapping_lessons = Lesson.objects.filter(
                date = self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk).exclude(status='CANCELLED')
        
            if overlapping_lessons.filter(self.teacher).exists():
                raise ValidationError('This lesson overlaps with another scheduled lesson.')
        

            if self.student:
                student_cnflicts = overlapping_lessons.filter(
                    models.Q(student=self.student) | models.Q(group__students=self.student)
                ).exists()

                if student_cnflicts.exists():
                    raise ValidationError('This lesson overlaps with another scheduled lesson for the assigned student.')


            if self.group and self.group.pk: # Для групового уроку
                # Отримуємо студентів групи і перевіряємо, чи немає в них накладок
                group_students = self.group.students.all()
                group_conflict = overlapping_lessons.filter(
                    models.Q(student__in=group_students) | models.Q(group__students__in=group_students)
                ).distinct().exists()

                if group_conflict:
                    raise ValidationError({"group": "Один або більше студентів з цієї групи мають інший урок у цей час."})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Викликаємо clean() перед збереженням
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

        if hasattr(self.lesson, 'student') and self.lesson.student and self.lesson.student != self.student:
            if self.lesson.status == 'CANCELLED':
                raise ValidationError('Cannot mark attendance for a cancelled lesson.')

            is_participant = False
            if self.lesson.student == self.student:
                is_participant = True
            elif self.lesson.group and self.lesson.group.students.filter(pk=self.student.pk).exists():
                is_participant = True

            if not is_participant:
                            raise ValidationError("Цього студента немає в списках на цей урок.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Присутній" if self.is_present else "Відсутній"
        return f"{self.student} - {self.lesson.date} ({status})"