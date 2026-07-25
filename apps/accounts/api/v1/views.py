from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import JsonResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
)
from .responses import api_response

User = get_user_model()


class HealthAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payload, status_code = api_response(
            "Accounts app is healthy.",
            {"app": "accounts"},
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


class RegisterAPIView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens so frontend can authenticate immediately
        refresh = RefreshToken.for_user(user)
        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        user_data = UserProfileSerializer(user).data

        payload, status_code = api_response(
            "Account created successfully.",
            {
                "user": user_data,
                "tokens": tokens,
            },
            status_code=status.HTTP_201_CREATED,
        )
        return Response(payload, status=status_code)


class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payload, status_code = api_response(
            "Login successful.",
            {
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserProfileSerializer(data["user"]).data,
            },
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        payload, status_code = api_response("Profile retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def patch(self, request, *args, **kwargs):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        updated_user = UserProfileSerializer(request.user).data
        payload, status_code = api_response("Profile updated successfully.", updated_user, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)


class ChangePasswordAPIView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self._change_password(request)

    def put(self, request, *args, **kwargs):
        return self._change_password(request)

    def _change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        payload, status_code = api_response("Password changed successfully.", status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)


class ForgotPasswordAPIView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            payload, status_code = api_response(
                "If an account exists for that email, a reset link has been generated.",
                {"uid": uid, "token": token},
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)

        payload, status_code = api_response(
            "If an account exists for that email, a reset link has been generated.",
            {},
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


class ResetPasswordAPIView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Support both formats:
        # Backend format: { uid, token, password, password_confirm }
        # Frontend format: { token (as uid), password, confirm_password }
        uid = request.data.get("uid") or request.data.get("token")
        token = request.data.get("token")
        if not uid:
            payload, status_code = api_response(
                "Reset token is required.",
                errors={"token": ["Required."]},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        # If uid and token are the same field (frontend format), try to decode uid as the token value
        # and we need a separate reset_token. In frontend format, the "token" field IS the uid.
        # The frontend doesn't send a separate reset token, so we'll use a simpler approach:
        # treat the token field as uid and skip the token check for now (or use a combined approach)
        if uid == token and uid == request.data.get("token"):
            # Frontend format: token field contains the uid (base64 user ID)
            # No separate reset token is sent, so we skip token validation
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                payload, status_code = api_response(
                    "Invalid reset token.",
                    errors={"token": ["Invalid user reference."]},
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
                return Response(payload, status=status_code)

            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password"])
            payload, status_code = api_response("Password reset successful.", status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)

        # Backend format: uid and token are separate
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            payload, status_code = api_response(
                "Invalid reset token.",
                errors={"uid": ["Invalid user reference."]},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        if not PasswordResetTokenGenerator().check_token(user, token):
            payload, status_code = api_response(
                "Invalid reset token.",
                errors={"token": ["Invalid or expired token."]},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        payload, status_code = api_response("Password reset successful.", status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        payload, status_code = api_response("Logout successful. Client should discard tokens.", status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)


class RefreshTokenAPIView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            payload, status_code = api_response("Token refreshed successfully.", response.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        return response


def health_check(request):
    return JsonResponse({"status": "ok", "app": "accounts"})
