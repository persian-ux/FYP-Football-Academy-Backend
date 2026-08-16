from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Match, MatchEvent, MatchResult, Team

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    coach_details = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "short_code",
            "description",
            "coach",
            "coach_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_coach_details(self, obj):
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
        if value and getattr(value, "role", None) != "coach":
            raise serializers.ValidationError(_("Team coach must have the coach role."))
        return value


class MatchEventSerializer(serializers.ModelSerializer):
    scorer_details = serializers.SerializerMethodField()
    assist_details = serializers.SerializerMethodField()

    class Meta:
        model = MatchEvent
        fields = [
            "id",
            "event_type",
            "team",
            "scorer",
            "scorer_name",
            "scorer_details",
            "minute",
            "assist",
            "assist_name",
            "assist_details",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_scorer_details(self, obj):
        if obj.scorer is None:
            return None
        return {
            "id": obj.scorer.id,
            "email": obj.scorer.email,
            "full_name": obj.scorer.get_full_name() or obj.scorer.email,
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_assist_details(self, obj):
        if obj.assist is None:
            return None
        return {
            "id": obj.assist.id,
            "email": obj.assist.email,
            "full_name": obj.assist.get_full_name() or obj.assist.email,
        }

    def validate(self, attrs):
        match = attrs.get("match") or getattr(self.instance, "match", None)
        team = attrs.get("team")
        if match is not None and team is not None:
            if team.pk not in (match.home_team_id, match.away_team_id):
                raise serializers.ValidationError(
                    _("Event team must be one of the match's participating teams.")
                )
        return attrs


class MatchResultSerializer(serializers.ModelSerializer):
    winner_display = serializers.CharField(source="get_winner_display", read_only=True)

    class Meta:
        model = MatchResult
        fields = [
            "id",
            "home_score",
            "away_score",
            "duration_minutes",
            "winner",
            "winner_display",
            "recorded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "winner", "recorded_by", "created_at", "updated_at"]


class MatchSerializer(serializers.ModelSerializer):
    home_team_details = TeamSerializer(source="home_team", read_only=True)
    away_team_details = TeamSerializer(source="away_team", read_only=True)
    result = MatchResultSerializer(read_only=True)
    events = MatchEventSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "home_team",
            "home_team_details",
            "away_team",
            "away_team_details",
            "match_date",
            "venue",
            "status",
            "status_display",
            "notes",
            "created_by",
            "result",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        home_team = attrs.get("home_team") or getattr(self.instance, "home_team", None)
        away_team = attrs.get("away_team") or getattr(self.instance, "away_team", None)
        if home_team is not None and away_team is not None and home_team.pk == away_team.pk:
            raise serializers.ValidationError(_("Home and away teams must be different."))
        return attrs


class MatchCompleteSerializer(serializers.Serializer):
    """Serializer for completing a match with final score and events."""

    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    duration_minutes = serializers.IntegerField(min_value=1, max_value=300, default=90)
    events = MatchEventSerializer(many=True, required=False)

    def validate(self, attrs):
        match = self.context.get("match")
        if match is None:
            raise serializers.ValidationError(_("Match context is required."))
        if match.status == Match.Status.COMPLETED:
            raise serializers.ValidationError(_("This match is already completed."))
        if match.status == Match.Status.CANCELLED:
            raise serializers.ValidationError(_("A cancelled match cannot be completed."))
        return attrs