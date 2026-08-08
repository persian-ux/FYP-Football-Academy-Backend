from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.players.models import Player


class Academy(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    academy = models.ForeignKey(
        Academy,
        on_delete=models.CASCADE,
        related_name="sections",
        blank=True,
        null=True,
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="coached_sections",
        blank=True,
        null=True,
        limit_choices_to={"role": "coach"},
    )
    players = models.ManyToManyField(
        Player,
        related_name="sections",
        blank=True,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Section"
        verbose_name_plural = "Sections"

    def __str__(self):
        return self.name