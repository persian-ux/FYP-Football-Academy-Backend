from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Match, MatchEvent, MatchResult, Team


class MatchSchedulingBaseTestCase(APITestCase):
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

        self.team_a = Team.objects.create(name="Team A", short_code="TA", coach=self.coach)
        self.team_b = Team.objects.create(name="Team B", short_code="TB")
        self.team_c = Team.objects.create(name="Team C", short_code="TC")

        self.match_list_url = reverse("match-list")
        self.team_list_url = reverse("team-list")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_match(self, home_team, away_team, days_from_now=1, **kwargs):
        return Match.objects.create(
            home_team=home_team,
            away_team=away_team,
            match_date=timezone.now() + timedelta(days=days_from_now),
            venue="Main Stadium",
            **kwargs,
        )


class TeamAPITests(MatchSchedulingBaseTestCase):
    def test_admin_can_create_team(self):
        self._auth(self.admin)
        response = self.client.post(
            self.team_list_url,
            {"name": "Team D", "short_code": "TD"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertTrue(Team.objects.filter(name="Team D").exists())

    def test_coach_cannot_create_team(self):
        self._auth(self.coach)
        response = self.client.post(
            self.team_list_url,
            {"name": "Team E", "short_code": "TE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_player_cannot_create_team(self):
        self._auth(self.player)
        response = self.client.post(
            self.team_list_url,
            {"name": "Team F", "short_code": "TF"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_roles_can_list_teams(self):
        for user in (self.admin, self.coach, self.player):
            self._auth(user)
            response = self.client.get(self.team_list_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json()["success"])


class MatchAPITests(MatchSchedulingBaseTestCase):
    def test_admin_can_create_match(self):
        self._auth(self.admin)
        response = self.client.post(
            self.match_list_url,
            {
                "home_team": self.team_a.pk,
                "away_team": self.team_b.pk,
                "match_date": (timezone.now() + timedelta(days=1)).isoformat(),
                "venue": "Main Stadium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Match.objects.count(), 1)

    def test_coach_can_create_match_for_coached_team(self):
        self._auth(self.coach)
        response = self.client.post(
            self.match_list_url,
            {
                "home_team": self.team_a.pk,
                "away_team": self.team_b.pk,
                "match_date": (timezone.now() + timedelta(days=1)).isoformat(),
                "venue": "Main Stadium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_player_cannot_create_match(self):
        self._auth(self.player)
        response = self.client.post(
            self.match_list_url,
            {
                "home_team": self.team_a.pk,
                "away_team": self.team_b.pk,
                "match_date": (timezone.now() + timedelta(days=1)).isoformat(),
                "venue": "Main Stadium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_create_match_with_same_team(self):
        self._auth(self.admin)
        response = self.client.post(
            self.match_list_url,
            {
                "home_team": self.team_a.pk,
                "away_team": self.team_a.pk,
                "match_date": (timezone.now() + timedelta(days=1)).isoformat(),
                "venue": "Main Stadium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_all_roles_can_list_matches(self):
        self._create_match(self.team_a, self.team_b)
        for user in (self.admin, self.coach, self.player):
            self._auth(user)
            response = self.client.get(self.match_list_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json()["success"])

    def test_filter_matches_by_team(self):
        self._create_match(self.team_a, self.team_b)
        self._create_match(self.team_b, self.team_c)
        self._auth(self.player)
        response = self.client.get(self.match_list_url, {"team": self.team_b.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 2)

    def test_filter_matches_by_status(self):
        self._create_match(self.team_a, self.team_b, status=Match.Status.SCHEDULED)
        self._create_match(self.team_b, self.team_c, status=Match.Status.CANCELLED)
        self._auth(self.player)
        response = self.client.get(self.match_list_url, {"status": "cancelled"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)

    def test_filter_matches_by_date(self):
        match = self._create_match(self.team_a, self.team_b, days_from_now=0)
        self._auth(self.player)
        date_str = timezone.localdate().strftime("%Y-%m-%d")
        response = self.client.get(self.match_list_url, {"date": date_str})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)

    def test_upcoming_matches_ordered_chronologically(self):
        self._create_match(self.team_a, self.team_b, days_from_now=2)
        self._create_match(self.team_b, self.team_c, days_from_now=1)
        self._create_match(self.team_a, self.team_c, days_from_now=3)
        self._auth(self.player)
        response = self.client.get(reverse("match-upcoming"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]["results"]
        dates = [item["match_date"] for item in data]
        self.assertEqual(dates, sorted(dates))

    def test_today_matches(self):
        self._create_match(self.team_a, self.team_b, days_from_now=0)
        self._create_match(self.team_b, self.team_c, days_from_now=1)
        self._auth(self.player)
        response = self.client.get(reverse("match-today"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)

    def test_results_only_completed(self):
        self._create_match(self.team_a, self.team_b, status=Match.Status.COMPLETED)
        self._create_match(self.team_b, self.team_c, status=Match.Status.SCHEDULED)
        self._auth(self.player)
        response = self.client.get(reverse("match-results"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["count"], 1)


class MatchResultAPITests(MatchSchedulingBaseTestCase):
    def test_admin_can_complete_match_home_win(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 3, "away_score": 1, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.COMPLETED)
        self.assertEqual(match.result.winner, MatchResult.Winner.HOME)

    def test_admin_can_complete_match_away_win(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 1, "away_score": 3, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.result.winner, MatchResult.Winner.AWAY)

    def test_admin_can_complete_match_draw(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 2, "away_score": 2, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.result.winner, MatchResult.Winner.DRAW)

    def test_winner_is_read_only_and_auto_calculated(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 3, "away_score": 1, "duration_minutes": 90, "winner": "away"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        # Winner is always auto-calculated, client cannot override
        self.assertEqual(match.result.winner, MatchResult.Winner.HOME)

    def test_coach_can_complete_coached_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.coach)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 1, "away_score": 0, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_player_cannot_complete_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.player)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 1, "away_score": 0, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_complete_cancelled_match(self):
        match = self._create_match(self.team_a, self.team_b, status=Match.Status.CANCELLED)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 1, "away_score": 0, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_complete_already_completed_match(self):
        match = self._create_match(self.team_a, self.team_b, status=Match.Status.COMPLETED)
        MatchResult.objects.create(match=match, home_score=1, away_score=0)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {"home_score": 2, "away_score": 1, "duration_minutes": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_match_with_goal_events(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-complete", kwargs={"pk": match.pk}),
            {
                "home_score": 2,
                "away_score": 1,
                "duration_minutes": 90,
                "events": [
                    {
                        "event_type": "goal",
                        "team": self.team_a.pk,
                        "scorer_name": "Player One",
                        "minute": 12,
                        "assist_name": "Player Two",
                    },
                    {
                        "event_type": "goal",
                        "team": self.team_a.pk,
                        "scorer_name": "Player Three",
                        "minute": 45,
                    },
                    {
                        "event_type": "goal",
                        "team": self.team_b.pk,
                        "scorer_name": "Player Four",
                        "minute": 78,
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.events.count(), 3)
        self.assertEqual(match.result.winner, MatchResult.Winner.HOME)

    def test_match_detail_includes_result_and_events(self):
        match = self._create_match(self.team_a, self.team_b, status=Match.Status.COMPLETED)
        MatchResult.objects.create(match=match, home_score=2, away_score=2)
        MatchEvent.objects.create(
            match=match,
            team=self.team_a,
            scorer_name="Player One",
            minute=10,
        )
        self._auth(self.player)
        response = self.client.get(reverse("match-detail", kwargs={"pk": match.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertEqual(data["result"]["home_score"], 2)
        self.assertEqual(data["result"]["away_score"], 2)
        self.assertEqual(data["result"]["winner"], "draw")
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["scorer_name"], "Player One")


class MatchLifecycleAPITests(MatchSchedulingBaseTestCase):
    def test_admin_can_reschedule_match(self):
        match = self._create_match(self.team_a, self.team_b)
        new_date = (timezone.now() + timedelta(days=5)).isoformat()
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-reschedule", kwargs={"pk": match.pk}),
            {"new_date": new_date, "new_venue": "Away Stadium"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.venue, "Away Stadium")

    def test_admin_can_postpone_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-postpone", kwargs={"pk": match.pk}),
            {"notes": "Weather conditions"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.POSTPONED)

    def test_admin_can_cancel_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-cancel", kwargs={"pk": match.pk}),
            {"notes": "Team unavailable"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.CANCELLED)

    def test_coach_can_reschedule_coached_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.coach)
        response = self.client.post(
            reverse("match-reschedule", kwargs={"pk": match.pk}),
            {"new_date": (timezone.now() + timedelta(days=5)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_player_cannot_cancel_match(self):
        match = self._create_match(self.team_a, self.team_b)
        self._auth(self.player)
        response = self.client.post(
            reverse("match-cancel", kwargs={"pk": match.pk}),
            {"notes": "Nope"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_reschedule_completed_match(self):
        match = self._create_match(self.team_a, self.team_b, status=Match.Status.COMPLETED)
        MatchResult.objects.create(match=match, home_score=1, away_score=0)
        self._auth(self.admin)
        response = self.client.post(
            reverse("match-reschedule", kwargs={"pk": match.pk}),
            {"new_date": (timezone.now() + timedelta(days=5)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)