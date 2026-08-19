"""Models for student performance reports."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.players.models import Player
from apps.scheduling.models import Match


class StudentReport(models.Model):
    """A student's (player's) performance report based on match performance.

    Admin can create, read, update and delete these reports. Each report
    records a student's individual match performance: goals, assists, total
    time played, fouls, yellow/red cards, plus additional useful stats.
    """

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="student_reports",
        verbose_name=_("Student"),
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.SET_NULL,
        related_name="student_reports",
        blank=True,
        null=True,
        verbose_name=_("Match"),
    )
    report_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Report Date"),
    )
    position = models.CharField(max_length=30, blank=True, null=True)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)
    fouls = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    shots = models.PositiveIntegerField(default=0)
    passes_completed = models.PositiveIntegerField(default=0)
    tackles = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        blank=True,
        null=True,
    )
    summary = models.TextField(blank=True, null=True)
    coach_remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_student_reports",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-report_date", "-created_at"]
        verbose_name = _("Student Report")
        verbose_name_plural = _("Student Reports")

    def __str__(self):
        return f"{self.player} report ({self.report_date})"