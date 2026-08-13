# type: ignore[attr-defined]
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import AttendanceRecord

User = get_user_model()


class AttendanceAPITestCase(TestCase):
    """Test suite for the Attendance Management API."""

    def setUp(self):
        self.admin = User.objects.create_user(  # type: ignore[call-arg]
            email="admin@test.com", password="pass12345", role=User.Role.ADMIN, is_staff=True  # type: ignore[attr-defined]
        )
        self.coach = User.objects.create_user(  # type: ignore[call-arg]
            email="coach@test.com", password="pass12345", role=User.Role.COACH  # type: ignore[attr-defined]
        )
        self.player = User.objects.create_user(  # type: ignore[call-arg]
            email="player@test.com", password="pass12345", role=User.Role.PLAYER  # type: ignore[attr-defined]
        )
        self.player2 = User.objects.create_user(  # type: ignore[call-arg]
            email="player2@test.com", password="pass12345", role=User.Role.PLAYER  # type: ignore[attr-defined]
        )

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

        self.coach_client = APIClient()
        self.coach_client.force_authenticate(user=self.coach)

        self.player_client = APIClient()
        self.player_client.force_authenticate(user=self.player)

        self.roster_url = reverse("attendance-roster")
        self.bulk_url = reverse("attendance-bulk")
        self.toggle_url = reverse("attendance-toggle")
        self.records_url = reverse("attendance-record-list")

    # ------------------------------------------------------------------
    # Roster endpoint
    # ------------------------------------------------------------------
    def test_roster_admin(self):
        resp = self.admin_client.get(self.roster_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()["data"]
        self.assertEqual(data["count"], 3)  # coach + 2 players (active)
        roles = {item["role"] for item in data["roster"]}
        self.assertEqual(roles, {"coach", "player"})

    def test_roster_with_date(self):
        resp = self.admin_client.get(self.roster_url, {"date": "2026-08-13"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_roster_invalid_date(self):
        resp = self.admin_client.get(self.roster_url, {"date": "invalid"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_roster_coach_forbidden(self):
        resp = self.coach_client.get(self.roster_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_roster_player_forbidden(self):
        resp = self.player_client.get(self.roster_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Bulk endpoint
    # ------------------------------------------------------------------
    def test_bulk_create(self):
        payload = {
            "date": "2026-08-13",
            "records": [
                {"user": self.player.id, "status": "present"},
                {"user": self.coach.id, "status": "absent"},
            ],
        }
        resp = self.admin_client.post(self.bulk_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["created"], 2)
        self.assertEqual(AttendanceRecord.objects.filter(date="2026-08-13").count(), 2)

    def test_bulk_update(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        payload = {
            "date": "2026-08-13",
            "records": [{"user": self.player.id, "status": "absent"}],
        }
        resp = self.admin_client.post(self.bulk_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["updated"], 1)
        self.player.refresh_from_db()
        record = AttendanceRecord.objects.get(user=self.player, date="2026-08-13")
        self.assertEqual(record.status, "absent")

    def test_bulk_invalid_status(self):
        payload = {
            "date": "2026-08-13",
            "records": [{"user": self.player.id, "status": "invalid"}],
        }
        resp = self.admin_client.post(self.bulk_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_admin_user_rejected(self):
        payload = {
            "date": "2026-08-13",
            "records": [{"user": self.admin.id, "status": "present"}],
        }
        resp = self.admin_client.post(self.bulk_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_coach_forbidden(self):
        payload = {
            "date": "2026-08-13",
            "records": [{"user": self.player.id, "status": "present"}],
        }
        resp = self.coach_client.post(self.bulk_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Toggle endpoint
    # ------------------------------------------------------------------
    def test_toggle_creates_present(self):
        resp = self.admin_client.post(
            self.toggle_url, {"user": self.player.id, "date": "2026-08-13"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["status"], "present")

    def test_toggle_present_to_absent(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        resp = self.admin_client.post(
            self.toggle_url, {"user": self.player.id, "date": "2026-08-13"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["status"], "absent")

    def test_toggle_coach_forbidden(self):
        resp = self.coach_client.post(
            self.toggle_url, {"user": self.player.id, "date": "2026-08-13"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # CRUD endpoints
    # ------------------------------------------------------------------
    def test_record_list_admin(self):
        resp = self.admin_client.get(self.records_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_record_list_coach_allowed(self):
        resp = self.coach_client.get(self.records_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_record_list_player_forbidden(self):
        resp = self.player_client.get(self.records_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_record_create_admin(self):
        payload = {"user": self.player.id, "date": "2026-08-15", "status": "present"}
        resp = self.admin_client.post(self.records_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()["data"]["marked_by"], self.admin.id)

    def test_record_create_duplicate_rejected(self):
        payload = {"user": self.player.id, "date": "2026-08-15", "status": "present"}
        self.admin_client.post(self.records_url, payload, format="json")
        resp = self.admin_client.post(self.records_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_record_create_coach_forbidden(self):
        payload = {"user": self.player.id, "date": "2026-08-15", "status": "present"}
        resp = self.coach_client.post(self.records_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_record_retrieve_admin(self):
        record = AttendanceRecord.objects.create(
            user=self.player, date="2026-08-15", status="present", marked_by=self.admin
        )
        resp = self.admin_client.get(reverse("attendance-record-detail", args=[record.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_record_update_admin(self):
        record = AttendanceRecord.objects.create(
            user=self.player, date="2026-08-15", status="present", marked_by=self.admin
        )
        resp = self.admin_client.patch(
            reverse("attendance-record-detail", args=[record.id]), {"status": "late"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["status"], "late")

    def test_record_update_coach_forbidden(self):
        record = AttendanceRecord.objects.create(
            user=self.player, date="2026-08-15", status="present", marked_by=self.admin
        )
        resp = self.coach_client.patch(
            reverse("attendance-record-detail", args=[record.id]), {"status": "late"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_record_delete_admin(self):
        record = AttendanceRecord.objects.create(
            user=self.player, date="2026-08-15", status="present", marked_by=self.admin
        )
        resp = self.admin_client.delete(reverse("attendance-record-detail", args=[record.id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_record_delete_coach_forbidden(self):
        record = AttendanceRecord.objects.create(
            user=self.player, date="2026-08-15", status="present", marked_by=self.admin
        )
        resp = self.coach_client.delete(reverse("attendance-record-detail", args=[record.id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_record_list_unauthenticated(self):
        anon = APIClient()
        resp = anon.get(self.records_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # Filtering & search
    # ------------------------------------------------------------------
    def test_record_filter_by_role(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        AttendanceRecord.objects.create(
            user=self.coach, date="2026-08-13", status="absent", marked_by=self.admin
        )
        resp = self.admin_client.get(self.records_url, {"role": "player"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["count"], 1)

    def test_record_filter_by_status(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        resp = self.admin_client.get(self.records_url, {"status": "present"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["count"], 1)

    def test_record_filter_by_date(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        resp = self.admin_client.get(self.records_url, {"date": "2026-08-13"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["count"], 1)

    def test_record_search(self):
        AttendanceRecord.objects.create(
            user=self.player, date="2026-08-13", status="present", marked_by=self.admin
        )
        resp = self.admin_client.get(self.records_url, {"search": "player@test.com"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["data"]["count"], 1)