from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import date, time

from Users.models import CustomUser
from Branches.models import Branch, Subject
from Students.models import Student
from Groups.models import Group, GroupMembership
from Lessons.models import Lesson


class GroupAPITests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Main Branch", city="Kyiv", address="1 Main St", status="active"
        )
        self.admin = CustomUser.objects.create_user(
            phone="+380990000001", password="adminpass", role="admin"
        )
        self.admin.branches.add(self.branch)

        self.teacher = CustomUser.objects.create_user(
            phone="+380990000002", password="teachpass",
            first_name="Ivan", last_name="Petrenko", role="teacher"
        )
        self.teacher.branches.add(self.branch)

        self.subject = Subject.objects.create(name="Math", branch=self.branch, status="active")

        self.student1 = Student.objects.create(
            first_name="Alice", last_name="Smith",
            phone="+380991111111", email="alice@test.com",
            address="Street 1", branch=self.branch, status="active"
        )
        self.student2 = Student.objects.create(
            first_name="Bob", last_name="Jones",
            phone="+380992222222", email="bob@test.com",
            address="Street 2", branch=self.branch, status="active"
        )
        self.group = Group.objects.create(
            name="Intermediate Math", branch=self.branch, status="active"
        )


    def test_admin_can_create_group(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-list")
        data = {"name": "Beginners English", "branch": self.branch.name, "status": "active"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Beginners English")

    def test_teacher_cannot_create_group(self):
        self.client.force_authenticate(user=self.teacher)
        data = {"name": "New Group", "branch": self.branch.name}
        response = self.client.post(reverse("group-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_groups(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("group-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_teacher_only_sees_groups_they_teach(self):
        Lesson.objects.create(
            title="Group Lesson", date=date(2026, 9, 1),
            start_time=time(10, 0), end_time=time(11, 0),
            teacher=self.teacher, subject=self.subject,
            branch=self.branch, group=self.group
        )
        other_group = Group.objects.create(
            name="Other Group", branch=self.branch, status="active"
        )

        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("group-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [g["id"] for g in response.data["results"]]
        self.assertIn(self.group.id, ids)
        self.assertNotIn(other_group.id, ids)

    def test_teacher_with_no_lessons_sees_no_groups(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("group-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)







    def test_delete_group_archives_it(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-detail", kwargs={"pk": self.group.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.status, "archived")

    def test_archived_group_not_in_list(self):
        self.group.status = "archived"
        self.group.save()
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("group-list"))
        ids = [g["id"] for g in response.data["results"]]
        self.assertNotIn(self.group.id, ids)





    def test_add_student_to_group(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-add-student", kwargs={"pk": self.group.id})
        response = self.client.post(url, {"student_id": self.student1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            GroupMembership.objects.filter(
                group=self.group, student=self.student1, leave_date__isnull=True
            ).exists()
        )

    def test_add_student_twice_is_idempotent(self):
        GroupMembership.objects.create(group=self.group, student=self.student1)
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-add-student", kwargs={"pk": self.group.id})
        response = self.client.post(url, {"student_id": self.student1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        count = GroupMembership.objects.filter(
            group=self.group, student=self.student1, leave_date__isnull=True
        ).count()
        self.assertEqual(count, 1)

    def test_remove_student_from_group(self):
        GroupMembership.objects.create(group=self.group, student=self.student1)
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-remove-student", kwargs={"pk": self.group.id})
        response = self.client.post(url, {"student_id": self.student1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership = GroupMembership.objects.get(group=self.group, student=self.student1)
        self.assertIsNotNone(membership.leave_date)

    def test_remove_student_not_in_group_fails(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-remove-student", kwargs={"pk": self.group.id})
        response = self.client.post(url, {"student_id": self.student2.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_student_from_different_branch(self):
        other_branch = Branch.objects.create(
            name="Other Branch", city="Lviv", address="2 Other St", status="active"
        )
        foreign_student = Student.objects.create(
            first_name="Carl", last_name="Sagan",
            phone="+380993333333", email="carl@test.com",
            address="Other St", branch=other_branch, status="active"
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse("group-add-student", kwargs={"pk": self.group.id})
        response = self.client.post(url, {"student_id": foreign_student.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
