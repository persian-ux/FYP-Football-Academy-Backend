from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.profiles.models import Profile


class Player(Profile):
    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="player_profile",
        unique=True,
    )
    profile_photo = models.ImageField(upload_to="players/photos/", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    emergency_contact = models.CharField(max_length=50, blank=True, null=True)
    guardian_name = models.CharField(max_length=150, blank=True, null=True)
    guardian_phone = models.CharField(max_length=20, blank=True, null=True)
    medical_information = models.TextField(blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    assigned_coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_players",
        blank=True,
        null=True,
        limit_choices_to={"role": User.Role.COACH},
    )
    assigned_sport = models.CharField(max_length=100, blank=True, null=True)
    academy_group = models.CharField(max_length=100, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    performance_notes = models.TextField(blank=True, null=True)
    attendance_summary = models.JSONField(default=dict, blank=True)
    statistics_summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"
