from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.validators import (
    validate_email_address,
    validate_password_strength,
    validate_phone_number,
    validate_role,
)

User = get_user_model()


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Create a user (player / coach) as an admin."""

    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        try:
            return validate_email_address(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_phone(self, value):
        if not value:
            return value
        try:
            return validate_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_role(self, value):
        try:
            return validate_role(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        if value == User.Role.ADMIN:
            raise serializers.ValidationError(
                _("Admin role cannot be created through this endpoint.")
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError({"password2": ["Passwords do not match."]})
        try:
            validate_password_strength(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone"),
            role=validated_data.get("role", User.Role.PLAYER),
            is_active=validated_data.get("is_active", True),
        )
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Update a user's profile / role / status as an admin."""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        try:
            return validate_email_address(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_phone(self, value):
        if not value:
            return value
        try:
            return validate_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def validate_role(self, value):
        try:
            return validate_role(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        if value == User.Role.ADMIN:
            raise serializers.ValidationError(
                _("Admin role cannot be assigned through this endpoint.")
            )
        return value

    def validate_password(self, value):
        if not value:
            return value
        try:
            return validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    """Read representation of a user for admin management."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "avatar",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = fields


class AdminUserStatusSerializer(serializers.ModelSerializer):
    """Activate / deactivate a user."""

    is_active = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ["is_active"]
        read_only_fields = []

    def validate_is_active(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError(_("is_active must be a boolean."))
        return value

    def update(self, instance, validated_data):
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save(update_fields=["is_active"])
        return instance
