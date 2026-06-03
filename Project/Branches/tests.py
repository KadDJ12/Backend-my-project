from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from Users.models import CustomUser
from Branches.models import Branch, Subject


class BranchAPITests(APITestCase):
 # Тести для філій

    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test Branch", city="Kyiv", address="1 Main St", status="active"
        )
        self.admin = CustomUser.objects.create_user(
            phone="+380990000001", password="adminpass", role="admin"
        )
        self.admin.branches.add(self.branch)

        self.teacher = CustomUser.objects.create_user(
            phone="+380990000002", password="teachpass",
            first_name="Ivan", last_name="Petrenko", role="teacher"
        )
#Доступи

    def test_teacher_cannot_access_branches(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("branch-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unauthenticated_cannot_access_branches(self):
        response = self.client.get(reverse("branch-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_admin_can_list_branches(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("branch-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


    def test_admin_can_create_branch(self):
        self.client.force_authenticate(user=self.admin)
        data = {"name": "New Branch", "city": "Lviv", "address": "2 Other St", "status": "active"}
        response = self.client.post(reverse("branch-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_admin_can_update_branch(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("branch-detail", kwargs={"pk": self.branch.id})
        response = self.client.patch(url, {"city": "Odesa"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.city, "Odesa")


#  Архівування 

    def test_admin_archives_empty_branch(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("branch-detail", kwargs={"pk": self.branch.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.status, "archived")


    def test_archived_branch_not_in_admin_queryset(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("branch-detail", kwargs={"pk": self.branch.id})
        self.client.delete(url)  
        response = self.client.get(reverse("branch-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)






class SubjectAPITests(APITestCase):
   # Тести для предметів 

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
            first_name="Olena", last_name="Koval", role="teacher"
        )
        self.subject = Subject.objects.create(
            name="Math", branch=self.branch, status="active"
        )


    def test_teacher_cannot_access_subjects(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("subject-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_can_list_subjects(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("subject-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)


    def test_admin_can_create_subject(self):
        self.client.force_authenticate(user=self.admin)
        data = {"name": "English", "branch": self.branch.name, "status": "active"}
        response = self.client.post(reverse("subject-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_delete_subject_archives_it(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("subject-detail", kwargs={"pk": self.subject.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.status, "archived")


    def test_archived_subject_hidden_from_list(self):
        # Архівуємо через API
        self.client.force_authenticate(user=self.admin)
        self.client.delete(reverse("subject-detail", kwargs={"pk": self.subject.id}))
        # Тепер в списку не має бути
        response = self.client.get(reverse("subject-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
