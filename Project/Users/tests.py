from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from Users.models import CustomUser
from Branches.models import Branch


class AuthTests(APITestCase):
    #JWT 

    def setUp(self):
        self.branch = Branch.objects.create(
            name="Main Branch", city="Kyiv", address="1 Main St", status="active"
        )
        self.admin = CustomUser.objects.create_user(
            phone="+380990000001", password="adminpass",
            first_name="Admin", last_name="User", role="admin"
        )
        self.admin.branches.add(self.branch)

        self.teacher = CustomUser.objects.create_user(
            phone="+380990000002", password="teachpass",
            first_name="Ivan", last_name="Petrenko", role="teacher"
        )


    def test_obtain_token_with_correct_credentials(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"phone": "+380990000001", "password": "adminpass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


    def test_obtain_token_wrong_password(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"phone": "+380990000001", "password": "wrongpass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_obtain_token_nonexistent_user(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"phone": "+380999999999", "password": "anypass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_me_returns_own_profile(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("customuser-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], "+380990000001")
        self.assertEqual(response.data["role"], "admin")

    def test_me_unauthenticated_returns_401(self):
        url = reverse("customuser-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_can_access_own_profile(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse("customuser-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "teacher")




    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("customuser-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_cannot_list_users(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse("customuser-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_teacher(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("customuser-list")
        data = {
            "first_name": "Oksana", "last_name": "Bondar",
            "phone": "+380993333333", "password": "securepass123",
            "role": "teacher"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "teacher")
