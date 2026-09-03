"""Serializers for student performance reports."""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.players.models import Player
from apps.scheduling.models import Match
from .models import StudentReport

User = get_user_model()


class StudentBriefSerializer(serializers.ModelSerializer):
    """Lightweight nested student (player) representation."""

    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "academy_group",
            "assigned_sport",
            "status",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class MatchBriefSerializer(serializers.ModelSerializer):
    """Lightweight nested match representation."""

    home_team_name = serializers.CharField(source="home_team.name", read_only=True)
    away_team_name = serializers.CharField(source="away_team.name", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "home_team",
            "home_team_name",
            "away_team",
            "away_team_name",
            "match_date",
            "venue",
            "status",
        ]
        read_only_fields = fields


class StudentReportSerializer(serializers.ModelSerializer):
    """A student's performance report with all key match statistics."""

    student_details = StudentBriefSerializer(source="player", read_only=True)
    match_details = MatchBriefSerializer(source="match", read_only=True)
    created_by_details = serializers.SerializerMethodField()

    class Meta:
        model = StudentReport
        fields = [
            "id",
            "player",
            "student_details",
            "match",
            "match_details",
            "report_date",
            "position",
            "goals",
            "assists",
            "minutes_played",
            "fouls",
            "yellow_cards",
            "red_cards",
            "shots",
            "passes_completed",
            "tackles",
            "saves",
            "rating",
            "summary",
            "coach_remarks",
            "created_by",
            "created_by_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "report_date", "created_by", "created_at", "updated_at"]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_created_by_details(self, obj):
        if obj.created_by is None:
            return None
        return {
            "id": obj.created_by.id,
            "email": obj.created_by.email,
            "full_name": obj.created_by.get_full_name() or obj.created_by.email,
        }

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user if request else None
        return super().create(validated_data)

    def validate_player(self, value):
        request = self.context.get("request")
        if request and request.user.role == User.Role.COACH and value.assigned_coach_id != request.user.id:
            raise serializers.ValidationError("You can only create reports for players assigned to you.")
        return value

    def validate_rating(self, value):
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("Rating must be between 0 and 10.")
        return value