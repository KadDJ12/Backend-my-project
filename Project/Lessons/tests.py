from rest_framework.test import APITestCase
from rest_framework import status
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import date, time
from Users.models import CustomUser
from Branches.models import Branch, Subject
from Students.models import Student
from Lessons.models import Lesson, LessonTemplate





#Конфлікти у розкладі
class LessonConflictTest(APITestCase):
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Main Branch", city="Lviv", status='active')
        self.subject = Subject.objects.create(name="Math", branch=self.branch, status='active')
        self.teacher = CustomUser.objects.create_user(
            phone="0981234567", password="password", first_name="John", last_name="Doe", role="teacher"
        )
        self.student = Student.objects.create(
            first_name="Alice", last_name="Smith", phone="0501112233",
            email="alice@test.com", branch=self.branch, status='active'
        )
        self.lesson1 = Lesson.objects.create(
            branch=self.branch, subject=self.subject, teacher=self.teacher,
            student=self.student, date=date(2026, 9, 1),
            start_time=time(10, 0), end_time=time(11, 0),
            status='SCHEDULED', title="First Math Lesson"
        )

    def test_teacher_conflict(self):
        student2 = Student.objects.create(
            first_name="Bob", last_name="Marley", phone="0509998877",
            email="bob@test.com", branch=self.branch, status='active'
        )
        overlapping = Lesson(
            branch=self.branch, subject=self.subject, teacher=self.teacher,
            student=student2, date=date(2026, 9, 1),
            start_time=time(10, 30), end_time=time(11, 30),
            status='SCHEDULED', title="Second Math Lesson"
        )
        with self.assertRaises(ValidationError):
            overlapping.clean()


    def test_student_conflict(self):
        teacher2 = CustomUser.objects.create_user(
            phone="0987654321", password="password", first_name="Jane", last_name="Doe", role="teacher"
        )
        overlapping = Lesson(
            branch=self.branch, subject=self.subject, teacher=teacher2,
            student=self.student, date=date(2026, 9, 1),
            start_time=time(10, 30), end_time=time(11, 30),
            status='SCHEDULED', title="Another Lesson"
        )
        with self.assertRaises(ValidationError):
            overlapping.clean()


# Доступ
class LessonAPITests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Main Branch", city="Kyiv", status="active")
        
        self.admin = CustomUser.objects.create_user(
            phone="+380998888888", password="adminpass", role="admin"
        )
        self.admin.branches.add(self.branch)

        self.teacher1 = CustomUser.objects.create_user(
            phone="+380991111111", password="teacherpass", role="teacher"
        )
        self.teacher1.branches.add(self.branch)

        self.teacher2 = CustomUser.objects.create_user(
            phone="+380992222222", password="teacherpass", role="teacher"
        )
        self.teacher2.branches.add(self.branch)
        self.subject = Subject.objects.create(name="Math", branch=self.branch, status="active")
        self.student1 = Student.objects.create(
            first_name="Charlie", email="charlie@test.com", branch=self.branch, status="active"
        )
        self.lesson_t1 = Lesson.objects.create(
            title="T1 Math", date=date(2026, 6, 10), start_time=time(10, 0), end_time=time(11, 0),
            teacher=self.teacher1, subject=self.subject, branch=self.branch, student=self.student1
        )
        self.lesson_t2 = Lesson.objects.create(
            title="T2 Math", date=date(2026, 6, 10), start_time=time(11, 0), end_time=time(12, 0),
            teacher=self.teacher2, subject=self.subject, branch=self.branch, student=self.student1
        )

    def test_teacher_only_sees_own_lessons(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(reverse('lesson-list'))
        self.assertEqual(response.status_code, 200)
        ids = [l['id'] for l in response.data['results']]
        self.assertIn(self.lesson_t1.id, ids)
        self.assertNotIn(self.lesson_t2.id, ids)


    def test_teacher_cannot_create_lesson(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {
            "title": "New Lesson", "date": "2026-07-01",
            "start_time": "09:00:00", "end_time": "10:00:00",
            "teacher": self.teacher1.id, "subject": self.subject.id,
            "branch": self.branch.id, "student": self.student1.id
        }
        response = self.client.post(reverse('lesson-list'), data, format='json')
        self.assertEqual(response.status_code, 403)





class LessonTemplateAPITests(APITestCase):
    # Tecти уроків
    def setUp(self):
        self.branch = Branch.objects.create(name="Main Branch", city="Kyiv", status="active")
        self.admin = CustomUser.objects.create_user(phone="+380998888888", password="adminpass", role="admin")
        self.admin.branches.add(self.branch)
        self.teacher = CustomUser.objects.create_user(phone="+380991111111", password="teacherpass", role="teacher")
        self.teacher.branches.add(self.branch)
        self.subject = Subject.objects.create(name="Math", branch=self.branch, status="active")
        self.student = Student.objects.create(first_name="Charlie", email="charlie@test.com", branch=self.branch, status="active")


    def _base_data(self, **overrides):
        data = {
            "branch": self.branch.id,
            "teacher": self.teacher.id,
            "subject": self.subject.id,
            "student": self.student.id,
            "days_of_week": [0, 2], # Понеділок та Середа
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "start_date": "2026-09-01",
            "end_date": "2026-09-14",
            "strategy": "skip",
        }
        data.update(overrides)
        return data


    def test_template_generates_lessons(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse('lesson-template-list'), self._base_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_count = response.data.get('lessons_created', 0)
        self.assertGreater(created_count, 0) 


    def test_template_start_after_end_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        data = self._base_data()
        data['start_date'] = '2026-09-30'
        data['end_date'] = '2026-09-01'
        response = self.client.post(reverse('lesson-template-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)