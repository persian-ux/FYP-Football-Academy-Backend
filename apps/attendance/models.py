from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AttendanceRecord(models.Model):
    """Tracks the presence of a player or coach on a given date."""

    class Status(models.TextChoices):
        PRESENT = "present", _("Present")
        ABSENT = "absent", _("Absent")
        LATE = "late", _("Late")
        EXCUSED = "excused", _("Excused")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("User"),
    )
    date = models.DateField(verbose_name=_("Date"))
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ABSENT,
        verbose_name=_("Status"),
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="attendance_marked",
        blank=True,
        null=True,
        verbose_name=_("Marked by"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = _("Attendance Record")
        verbose_name_plural = _("Attendance Records")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="unique_attendance_per_user_per_day",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.date} - {self.status}"