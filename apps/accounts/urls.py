from django.urls import path

from .api.v1.admin_views import (
    AdminCoachListAPIView,
    AdminPlayerListAPIView,
    AdminUserCreateAPIView,
    AdminUserDetailAPIView,
    AdminUserListAPIView,
    AdminUserStatusAPIView,
)
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
    # Admin user management (CRUD for coaches & players)
    path("admin/users/", AdminUserListAPIView.as_view(), name="admin-user-list"),
    path("admin/users/create/", AdminUserCreateAPIView.as_view(), name="admin-user-create"),
    path("admin/users/<int:pk>/", AdminUserDetailAPIView.as_view(), name="admin-user-detail"),
    path("admin/users/<int:pk>/status/", AdminUserStatusAPIView.as_view(), name="admin-user-status"),
    path("admin/coaches/", AdminCoachListAPIView.as_view(), name="admin-coach-list"),
    path("admin/players/", AdminPlayerListAPIView.as_view(), name="admin-player-list"),
]