from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.accounts.validators import validate_email_address, validate_phone_number
from .models import Player

User = get_user_model()


class PlayerUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

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
            "password",
        ]
        read_only_fields = ["id", "is_active"]

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
        if value not in {User.Role.PLAYER}:
            raise serializers.ValidationError(_("Only player role can be created through this endpoint."))
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone"),
            role=User.Role.PLAYER,
        )


class PlayerSerializer(serializers.ModelSerializer):
    user = PlayerUserSerializer(required=False)
    assigned_coach = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.COACH),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Player
        fields = [
            "id",
            "user",
            "profile_photo",
            "date_of_birth",
            "gender",
            "emergency_contact",
            "guardian_name",
            "guardian_phone",
            "medical_information",
            "blood_group",
            "address",
            "assigned_coach",
            "assigned_sport",
            "academy_group",
            "joining_date",
            "status",
            "performance_notes",
            "attendance_summary",
            "statistics_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_assigned_coach(self, value):
        if value and getattr(value, "role", None) != User.Role.COACH:
            raise serializers.ValidationError(_("Assigned coach must have the coach role."))
        return value

    def create(self, validated_data):
        nested_user = validated_data.pop("user", None)
        if not nested_user:
            raise serializers.ValidationError({"user": [_("This field is required.")]})

        user = PlayerUserSerializer().create(nested_user)
        player = Player.objects.create(user=user, **validated_data)
        return player

    def update(self, instance, validated_data):
        nested_user = validated_data.pop("user", None)
        if nested_user:
            user_serializer = PlayerUserSerializer(instance.user, data=nested_user, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
