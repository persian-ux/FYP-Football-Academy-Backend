from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .validators import validate_email_address, validate_phone_number, validate_role, validate_password_strength


class BaseResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)
    errors = serializers.JSONField(required=False, allow_null=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirmPassword = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    firstName = serializers.CharField(required=False, allow_blank=True, max_length=150)
    lastName = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phoneNumber = serializers.CharField(required=False, allow_blank=True, max_length=20)

    class Meta:
        model = User
        fields = [
            "email", "password",
            "password2", "confirm_password", "password_confirm", "confirmPassword",
            "first_name", "last_name", "firstName", "lastName",
            "phone", "phoneNumber", "role",
        ]

    def validate(self, attrs):
        email = validate_email_address(attrs.get("email", ""))
        phone = validate_phone_number(attrs.get("phone", "")) if attrs.get("phone") or attrs.get("phoneNumber") else None
        role = validate_role(attrs.get("role", "player"))
        password = attrs.get("password")

        # Support multiple field names for password confirmation:
        # password2 (backend), confirm_password (common), password_confirm (alternative), confirmPassword (frontend camelCase)
        confirm = attrs.get("confirm_password") or attrs.get("password_confirm") or attrs.get("password2") or attrs.get("confirmPassword")
        if not confirm:
            raise serializers.ValidationError({"confirm_password": ["Password confirmation is required."]})
        if password != confirm:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})

        try:
            validate_password_strength(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        attrs["email"] = email
        attrs["phone"] = phone
        attrs["role"] = role
        # Map camelCase first/last names to snake_case
        if not attrs.get("first_name") and attrs.get("firstName"):
            attrs["first_name"] = attrs["firstName"]
        if not attrs.get("last_name") and attrs.get("lastName"):
            attrs["last_name"] = attrs["lastName"]
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        validated_data.pop("confirm_password", None)
        validated_data.pop("password_confirm", None)
        validated_data.pop("confirmPassword", None)
        validated_data.pop("firstName", None)
        validated_data.pop("lastName", None)
        validated_data.pop("phoneNumber", None)
        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            phone=validated_data.get("phone"),
            role=validated_data.get("role"),
        )
        user.first_name = validated_data.get("first_name", "")
        user.last_name = validated_data.get("last_name", "")
        user.save(update_fields=["first_name", "last_name"])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = validate_email_address(attrs.get("email", ""))
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if not user or not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["Invalid email or password."]})

        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=False, write_only=True, allow_blank=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs.get("old_password")):
            raise serializers.ValidationError({"old_password": ["Current password is incorrect."]})

        # Support both field names: confirm_password (backend) and confirm_new_password (frontend)
        confirm = attrs.get("confirm_new_password") or attrs.get("confirm_password")
        if attrs.get("new_password") != confirm:
            raise serializers.ValidationError({"confirm_new_password": ["Passwords do not match."]})

        try:
            validate_password_strength(attrs.get("new_password"))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "role", "avatar"]

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate_role(self, value):
        return validate_role(value)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return validate_email_address(value)


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)
    password_confirm = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=False, write_only=True, allow_blank=True)

    def validate(self, attrs):
        # Support both field names: password_confirm (backend) and confirm_password (frontend)
        confirm = attrs.get("confirm_password") or attrs.get("password_confirm")
        if attrs.get("password") != confirm:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})

        try:
            validate_password_strength(attrs.get("password"))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "avatar", "is_active", "date_joined"]
        read_only_fields = fields
