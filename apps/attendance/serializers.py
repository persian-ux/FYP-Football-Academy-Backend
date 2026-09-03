from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.models import User

from .models import AttendanceRecord

# Roles that can be marked for attendance (players and coaches)
ATTENDANCE_ROLES = [User.Role.PLAYER, User.Role.COACH]


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for a single attendance record (CRUD)."""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    marked_by_name = serializers.CharField(source="marked_by.get_full_name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "user_role",
            "date",
            "status",
            "marked_by",
            "marked_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "marked_by", "created_at", "updated_at"]

    def validate_user(self, value):
        if value.role not in ATTENDANCE_ROLES:
            raise serializers.ValidationError(
                _("Attendance can only be marked for players and coaches.")
            )
        request = self.context.get("request")
        if request and request.user.role == User.Role.COACH:
            player_profile = getattr(value, "player_profile", None)
            is_assigned_player = value.role == User.Role.PLAYER and player_profile is not None and player_profile.assigned_coach_id == request.user.id
            if value != request.user and not is_assigned_player:
                raise serializers.ValidationError(_("You can only manage your own or assigned players' attendance."))
        return value

    def validate_status(self, value):
        if value not in AttendanceRecord.Status.values:
            raise serializers.ValidationError(
                _("Invalid attendance status. Choose from: %(choices)s.")
                % {"choices": ", ".join(AttendanceRecord.Status.values)}
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["marked_by"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["marked_by"] = request.user
        return super().update(instance, validated_data)


class AttendanceRosterItemSerializer(serializers.Serializer):
    """A single roster entry combining a user with their attendance status."""

    user_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    status = serializers.CharField()
    attendance_id = serializers.IntegerField(allow_null=True)


class AttendanceBulkItemSerializer(serializers.Serializer):
    """A single item inside a bulk attendance payload."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=ATTENDANCE_ROLES)
    )
    status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)


class AttendanceBulkSerializer(serializers.Serializer):
    """Bulk mark attendance for multiple users on a single date."""

    date = serializers.DateField()
    records = AttendanceBulkItemSerializer(many=True, allow_empty=False)

    def validate_records(self, value):
        request = self.context.get("request")
        if request and request.user.role == User.Role.COACH:
            for item in value:
                user = item["user"]
                player_profile = getattr(user, "player_profile", None)
                is_assigned_player = user.role == User.Role.PLAYER and player_profile is not None and player_profile.assigned_coach_id == request.user.id
                if user != request.user and not is_assigned_player:
                    raise serializers.ValidationError(_("You can only manage your own or assigned players' attendance."))
        return value


class AttendanceToggleSerializer(serializers.Serializer):
    """Toggle a single user's attendance between present and absent."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=ATTENDANCE_ROLES)
    )
    date = serializers.DateField()

    def validate_user(self, value):
        request = self.context.get("request")
        if request and request.user.role == User.Role.COACH:
            player_profile = getattr(value, "player_profile", None)
            is_assigned_player = value.role == User.Role.PLAYER and player_profile is not None and player_profile.assigned_coach_id == request.user.id
            if value != request.user and not is_assigned_player:
                raise serializers.ValidationError(_("You can only manage your own or assigned players' attendance."))
        return value