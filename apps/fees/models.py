from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.players.models import Player


class FeeRecord(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", _("Unpaid")
        PAID = "paid", _("Paid")
        PENDING = "pending", _("Pending")
        OVERDUE = "overdue", _("Overdue")

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="fee_records")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fee Record"
        verbose_name_plural = "Fee Records"

    def __str__(self):
        return f"{self.player} - {self.amount} ({self.status})"
