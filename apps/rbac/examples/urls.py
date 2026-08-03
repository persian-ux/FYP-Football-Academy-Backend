from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"users", views.UserProfileViewSet, basename="rbac-user")

urlpatterns = [
    path("admin-only/", views.AdminOnlyAPIView.as_view(), name="rbac-admin-only"),
    path("coach-only/", views.CoachOnlyAPIView.as_view(), name="rbac-coach-only"),
    path("player-only/", views.PlayerOnlyAPIView.as_view(), name="rbac-player-only"),
    path("staff-only/", views.StaffOnlyAPIView.as_view(), name="rbac-staff-only"),
    path("my-profile/", views.MyProfileAPIView.as_view(), name="rbac-my-profile"),
    path("", include(router.urls)),
]

