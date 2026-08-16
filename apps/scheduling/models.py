from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Team(models.Model):
    """An academy team that participates in scheduled matches."""

    name = models.CharField(max_length=150, unique=True)
    short_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="coached_teams",
        blank=True,
        null=True,
        limit_choices_to={"role": "coach"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return self.name


class Match(models.Model):
    """A scheduled football match between two different academy teams."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        POSTPONED = "postponed", _("Postponed")
        CANCELLED = "cancelled", _("Cancelled")
        COMPLETED = "completed", _("Completed")

    home_team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="home_matches",
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="away_matches",
    )
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_matches",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["match_date"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(home_team=models.F("away_team")),
                name="match_home_away_teams_different",
            ),
        ]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} @ {self.match_date:%Y-%m-%d %H:%M}"

    def clean(self):
        super().clean()
        home_team_id = getattr(self, "home_team_id", None)
        away_team_id = getattr(self, "away_team_id", None)
        if home_team_id and away_team_id and home_team_id == away_team_id:
            raise ValidationError(_("Home and away teams must be different."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class MatchResult(models.Model):
    """Final result of a completed match. Winner is auto-calculated from scores."""

    class Winner(models.TextChoices):
        HOME = "home", _("Home Team")
        AWAY = "away", _("Away Team")
        DRAW = "draw", _("Draw")

    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name="result",
    )
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=90)
    winner = models.CharField(
        max_length=10,
        choices=Winner.choices,
        editable=False,
        blank=True,
        null=True,
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_results",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Match Result"
        verbose_name_plural = "Match Results"

    def __str__(self):
        return f"{self.match} — {self.home_score}-{self.away_score}"

    def calculate_winner(self):
        """Automatically determine the winner from the final score."""
        if self.home_score > self.away_score:
            return self.Winner.HOME
        if self.away_score > self.home_score:
            return self.Winner.AWAY
        return self.Winner.DRAW

    def save(self, *args, **kwargs):
        self.winner = self.calculate_winner()
        super().save(*args, **kwargs)


class MatchEvent(models.Model):
    """A basic match event (goal) recorded for a completed match."""

    class EventType(models.TextChoices):
        GOAL = "goal", _("Goal")

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.GOAL,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="match_events",
    )
    scorer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="scored_events",
        blank=True,
        null=True,
    )
    scorer_name = models.CharField(max_length=150, blank=True, null=True)
    minute = models.PositiveIntegerField()
    assist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assisted_events",
        blank=True,
        null=True,
    )
    assist_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["minute"]
        verbose_name = "Match Event"
        verbose_name_plural = "Match Events"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(minute__lte=120),
                name="match_event_minute_max_120",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} by {self.scorer_name or self.scorer} ({self.minute}')"