from django.urls import path

from .api.v1.views import (
    ChangePasswordAPIView,
    ForgotPasswordAPIView,
    HealthAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
    ResetPasswordAPIView,
    health_check,
)

urlpatterns = [
    path("health/", health_check, name="accounts-health"),
    path("health-api/", HealthAPIView.as_view(), name="accounts-health-api"),
    path("register/", RegisterAPIView.as_view(), name="accounts-register"),
    path("login/", LoginAPIView.as_view(), name="accounts-login"),
    path("logout/", LogoutAPIView.as_view(), name="accounts-logout"),
    path("refresh/", RefreshTokenAPIView.as_view(), name="accounts-refresh"),
    path("profile/", ProfileAPIView.as_view(), name="accounts-profile"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="accounts-change-password"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="accounts-forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="accounts-reset-password"),
]
