from typing import Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.players.models import Player
from .models import Academy, Section

User = get_user_model()


class AcademySerializer(serializers.ModelSerializer):
    class Meta:
        model = Academy
        fields = ["id", "name", "location", "created_at"]
        read_only_fields = ["id", "created_at"]


class SectionPlayerSerializer(serializers.ModelSerializer):
    """Lightweight player representation used inside a Section."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ["id", "full_name", "status", "assigned_sport", "academy_group"]
        read_only_fields = fields

    def get_full_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.user.email


class SectionSerializer(serializers.ModelSerializer):
    coach = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.COACH),
        required=False,
        allow_null=True,
    )
    coach_details = serializers.SerializerMethodField()
    academy = serializers.PrimaryKeyRelatedField(
        queryset=Academy.objects.all(),
        required=False,
        allow_null=True,
    )
    academy_details = AcademySerializer(source="academy", read_only=True)
    players = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False,
    )
    players_details = SectionPlayerSerializer(source="players", many=True, read_only=True)
    player_count = serializers.IntegerField(source="players.count", read_only=True)

    class Meta:
        model = Section
        fields = [
            "id",
            "name",
            "description",
            "academy",
            "academy_details",
            "coach",
            "coach_details",
            "players",
            "players_details",
            "player_count",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_coach_details(self, obj) -> Optional[dict]:
        if obj.coach is None:
            return None
        return {
            "id": obj.coach.id,
            "email": obj.coach.email,
            "first_name": obj.coach.first_name,
            "last_name": obj.coach.last_name,
            "full_name": obj.coach.get_full_name() or obj.coach.email,
        }

    def validate_coach(self, value):
        if value and getattr(value, "role", None) != User.Role.COACH:
            raise serializers.ValidationError(_("Assigned coach must have the coach role."))
        return value

    def validate_players(self, value):
        for player in value:
            if not isinstance(player, Player):
                raise serializers.ValidationError(_("Each player must be a valid player."))
        return value