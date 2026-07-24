from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AccountAuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("accounts-register")
        self.login_url = reverse("accounts-login")
        self.profile_url = reverse("accounts-profile")
        self.change_password_url = reverse("accounts-change-password")

    def test_register_and_login_flow(self):
        register_payload = {
            "email": "player@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "phone": "+1234567890",
            "role": "player",
        }

        response = self.client.post(self.register_url, register_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="player@example.com").exists())

        login_payload = {
            "email": "player@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(self.login_url, login_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json()["data"])
        self.assertIn("refresh", response.json()["data"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access']}")
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        change_payload = {
            "old_password": "StrongPass123!",
            "new_password": "NewStrongPass123!",
            "confirm_password": "NewStrongPass123!",
        }

        password_response = self.client.post(self.change_password_url, change_payload, format="json")
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)
