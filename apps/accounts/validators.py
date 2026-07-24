import re

from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


def validate_email_address(email: str) -> str:
    if not email or not email.strip():
        raise ValidationError("Email is required.")

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, email.strip()):
        raise ValidationError("Enter a valid email address.")
    return email.strip().lower()


def validate_phone_number(phone: str) -> str:
    if phone is None:
        return ""
    phone = phone.strip()
    if not phone:
        return ""

    if not re.match(r"^\+?[0-9\s\-]{7,20}$", phone):
        raise ValidationError("Enter a valid phone number.")
    return phone


def validate_role(role: str) -> str:
    valid_roles = {"player", "coach", "admin"}
    if role not in valid_roles:
        raise ValidationError("Role must be one of: player, coach, admin.")
    return role


def validate_password_strength(password: str) -> str:
    try:
        validate_password(password)
    except ValidationError as exc:
        raise ValidationError(list(exc.messages))
    return password
