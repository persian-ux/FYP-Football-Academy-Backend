"""Tests for student performance reports API."""

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.players.models import Player
from apps.scheduling.models import Match, MatchResult, Team
from .models import StudentReport


class StudentReportBaseTestCase(APITestCase):
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
        self.player_user = User.objects.create_user(
            email="player@academy.test",
            password="StrongPass123!",
            role=User.Role.PLAYER,
        )
        self.other_player_user = User.objects.create_user(
            email="other@academy.test",
            password="StrongPass123!",
            role=User.Role.PLAYER,
        )

        self.player = Player.objects.create(
            user=self.player_user,
            assigned_coach=self.coach,
            academy_group="U-15",
            assigned_sport="Football",
        )
        self.other_player = Player.objects.create(
            user=self.other_player_user,
            assigned_coach=self.coach,
            academy_group="U-15",
            assigned_sport="Football",
        )

        self.team_a = Team.objects.create(name="Team A", short_code="TA")
        self.team_b = Team.objects.create(name="Team B", short_code="TB")

        self.match = Match.objects.create(
            home_team=self.team_a,
            away_team=self.team_b,
            match_date=timezone.now() - timedelta(days=1),
            venue="Main Stadium",
            status=Match.Status.COMPLETED,
        )
        MatchResult.objects.create(match=self.match, home_score=2, away_score=1)

        self.report_list_url = reverse("student-report-list")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_report(self, **kwargs):
        return StudentReport.objects.create(
            player=kwargs.get("player", self.player),
            match=kwargs.get("match", self.match),
            position=kwargs.get("position", "Forward"),
            goals=kwargs.get("goals", 1),
            assists=kwargs.get("assists", 0),
            minutes_played=kwargs.get("minutes_played", 90),
            fouls=kwargs.get("fouls", 0),
            yellow_cards=kwargs.get("yellow_cards", 0),
            red_cards=kwargs.get("red_cards", 0),
            rating=kwargs.get("rating", Decimal("7.5")),
            created_by=self.admin,
        )


class StudentReportAPITests(StudentReportBaseTestCase):
    def test_admin_can_create_student_report(self):
        self._auth(self.admin)
        response = self.client.post(
            self.report_list_url,
            {
                "player": self.player.pk,
                "match": self.match.pk,
                "position": "Forward",
                "goals": 3,
                "assists": 2,
                "minutes_played": 90,
                "fouls": 1,
                "yellow_cards": 0,
                "red_cards": 0,
                "shots": 5,
                "passes_completed": 25,
                "tackles": 4,
                "saves": 0,
                "rating": "8.5",
                "summary": "Excellent performance",
                "coach_remarks": "Great game",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertEqual(StudentReport.objects.count(), 1)
        report = StudentReport.objects.get()
        self.assertEqual(report.player_id, self.player.id)
        self.assertEqual(report.goals, 3)
        self.assertEqual(report.assists, 2)
        self.assertEqual(report.minutes_played, 90)
        self.assertEqual(report.fouls, 1)
        self.assertEqual(report.yellow_cards, 0)
        self.assertEqual(report.red_cards, 0)
        self.assertEqual(report.created_by, self.admin)

    def test_coach_can_create_student_report_for_assigned_player(self):
        self._auth(self.coach)
        response = self.client.post(
            self.report_list_url,
            {"player": self.player.id, "goals": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_player_cannot_create_student_report(self):
        self._auth(self.player_user)
        response = self.client.post(
            self.report_list_url,
            {"player": self.player.id, "goals": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_roles_can_list_student_reports(self):
        self._create_report()
        for user in (self.admin, self.coach, self.player_user):
            self._auth(user)
            response = self.client.get(self.report_list_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json()["success"])

    def test_filter_reports_by_player(self):
        self._create_report(player=self.player)
        self._create_report(player=self.other_player)
        self._auth(self.admin)
        response = self.client.get(self.report_list_url, {"player": self.player.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)

    def test_filter_reports_by_match(self):
        self._create_report(match=self.match)
        self._auth(self.admin)
        response = self.client.get(self.report_list_url, {"match": self.match.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)

    def test_admin_can_retrieve_student_report(self):
        report = self._create_report(goals=2, assists=1)
        self._auth(self.admin)
        response = self.client.get(reverse("student-report-detail", kwargs={"pk": report.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertEqual(data["goals"], 2)
        self.assertEqual(data["assists"], 1)
        self.assertEqual(data["player"], self.player.id)
        self.assertEqual(data["match"], self.match.id)
        self.assertIn("student_details", data)
        self.assertIn("match_details", data)

    def test_admin_can_update_student_report(self):
        report = self._create_report(goals=1)
        self._auth(self.admin)
        response = self.client.patch(
            reverse("student-report-detail", kwargs={"pk": report.pk}),
            {"goals": 4, "assists": 3, "yellow_cards": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.goals, 4)
        self.assertEqual(report.assists, 3)
        self.assertEqual(report.yellow_cards, 1)

    def test_admin_can_delete_student_report(self):
        report = self._create_report()
        self._auth(self.admin)
        response = self.client.delete(reverse("student-report-detail", kwargs={"pk": report.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentReport.objects.filter(pk=report.pk).exists())

    def test_rating_validation(self):
        self._auth(self.admin)
        response = self.client.post(
            self.report_list_url,
            {"player": self.player.id, "rating": "11.0"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_requires_player(self):
        self._auth(self.admin)
        response = self.client.post(
            self.report_list_url,
            {"goals": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
