from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Player


class PlayerManagementAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@academy.test",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )
        self.coach = User.objects.create_user(
            email="coach@academy.test",
            password="StrongPass123!",
            role=User.Role.COACH,
        )
        self.player = User.objects.create_user(
            email="player@academy.test",
            password="StrongPass123!",
            role=User.Role.PLAYER,
        )
        self.list_url = reverse("player-list")
        self.detail_url = reverse("player-detail", kwargs={"pk": 1})

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_can_create_player_and_list_players(self):
        self._auth(self.admin)
        payload = {
            "user": {
                "email": "newplayer@academy.test",
                "password": "StrongPass123!",
                "role": "player",
                "first_name": "New",
                "last_name": "Player",
                "phone": "+1234567890",
            },
            "date_of_birth": "2012-05-14",
            "gender": "male",
            "emergency_contact": "+1111111111",
            "guardian_name": "Guardian Name",
            "guardian_phone": "+2222222222",
            "medical_information": "No known allergies",
            "blood_group": "O+",
            "address": "1 Academy Road",
            "assigned_sport": "Football",
            "academy_group": "U15",
            "joining_date": "2026-08-01",
            "status": "active",
            "performance_notes": "Excellent work rate",
        }

        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertTrue(Player.objects.filter(user__email="newplayer@academy.test").exists())

        listing = self.client.get(self.list_url, {"search": "newplayer"})
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(listing.json()["data"]["count"], 1)

    def test_coach_can_only_update_performance_notes_for_assigned_player(self):
        self._auth(self.coach)
        player = Player.objects.create(
            user=self.player,
            assigned_coach=self.coach,
            date_of_birth=date(2012, 5, 14),
            gender="male",
            emergency_contact="+1111111111",
            guardian_name="Guardian Name",
            guardian_phone="+2222222222",
            medical_information="No known allergies",
            blood_group="O+",
            address="1 Academy Road",
            assigned_sport="Football",
            academy_group="U15",
            joining_date=date(2026, 8, 1),
            status="active",
            performance_notes="Initial note",
        )

        response = self.client.patch(
            reverse("player-detail", kwargs={"pk": player.pk}),
            {"performance_notes": "Updated note"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        player.refresh_from_db()
        self.assertEqual(player.performance_notes, "Updated note")

    def test_player_can_view_and_update_own_profile_only(self):
        self._auth(self.player)
        player = Player.objects.create(
            user=self.player,
            date_of_birth=date(2012, 5, 14),
            gender="male",
            emergency_contact="+1111111111",
            guardian_name="Guardian Name",
            guardian_phone="+2222222222",
            medical_information="No known allergies",
            blood_group="O+",
            address="1 Academy Road",
            assigned_sport="Football",
            academy_group="U15",
            joining_date=date(2026, 8, 1),
            status="active",
            performance_notes="Initial note",
        )

        response = self.client.get(reverse("player-detail", kwargs={"pk": player.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patch_response = self.client.patch(
            reverse("player-detail", kwargs={"pk": player.pk}),
            {"address": "2 Academy Road"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        player.refresh_from_db()
        self.assertEqual(player.address, "2 Academy Road")
