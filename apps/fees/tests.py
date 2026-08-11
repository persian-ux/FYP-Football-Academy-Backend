from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.players.models import Player
from .models import FeeRecord


class FeeManagementAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@academy.test",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )
        self.player_user = User.objects.create_user(
            email="student@academy.test",
            password="StrongPass123!",
            role=User.Role.PLAYER,
            first_name="Student",
            last_name="One",
        )
        self.player = Player.objects.create(
            user=self.player_user,
            date_of_birth=date(2012, 5, 14),
            gender="male",
            guardian_name="Guardian One",
            guardian_phone="+1234567890",
            assigned_sport="Football",
            academy_group="U15",
            joining_date=date(2026, 8, 1),
            status="active",
        )
        self.list_url = reverse("fee-list")
        self.students_url = reverse("fee-students")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_can_load_students_with_fee_state(self):
        self._auth(self.admin)
        response = self.client.get(self.students_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        self.assertGreaterEqual(len(response.json()["data"]), 1)

    def test_admin_can_create_update_and_delete_fee_record(self):
        self._auth(self.admin)

        create_response = self.client.post(
            self.list_url,
            {"player": self.player.pk, "amount": "250.00", "status": "unpaid"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.json()["success"])

        fee = FeeRecord.objects.get(player=self.player)
        patch_response = self.client.patch(
            reverse("fee-detail", kwargs={"pk": fee.pk}),
            {"status": "paid"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        fee.refresh_from_db()
        self.assertEqual(fee.status, "paid")

        delete_response = self.client.delete(reverse("fee-detail", kwargs={"pk": fee.pk}))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FeeRecord.objects.filter(pk=fee.pk).exists())
