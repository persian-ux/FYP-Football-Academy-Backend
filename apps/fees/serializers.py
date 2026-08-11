from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.players.models import Player
from .models import FeeRecord

User = get_user_model()


class FeeRecordSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.select_related("user").all())
    student_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()

    class Meta:
        model = FeeRecord
        fields = [
            "id",
            "player",
            "student_name",
            "student_email",
            "amount",
            "status",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "student_name", "student_email"]

    def get_student_name(self, obj):
        return obj.player.user.get_full_name() or obj.player.user.email

    def get_student_email(self, obj):
        return obj.player.user.email

    def validate_player(self, value):
        if value is None:
            raise ValidationError("A player is required.")
        return value

    def validate_status(self, value):
        normalized = str(value or "").strip().lower()
        if normalized in {"pending", "unpaid"}:
            return FeeRecord.Status.UNPAID
        if normalized in {"paid"}:
            return FeeRecord.Status.PAID
        if normalized in {"overdue"}:
            return FeeRecord.Status.OVERDUE
        raise ValidationError("Status must be one of: paid, unpaid, pending, overdue.")

    def validate_amount(self, value):
        if value is None:
            raise ValidationError("Amount is required.")
        return value
