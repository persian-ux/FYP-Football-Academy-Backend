from rest_framework import serializers

from apps.accounts.models import User


class UserReadOnlySerializer(serializers.ModelSerializer):
    """Read-only representation of a user used by the RBAC example views."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "is_active", "date_joined"]
        read_only_fields = fields

