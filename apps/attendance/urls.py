from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceBulkAPIView,
    AttendanceRosterAPIView,
    AttendanceToggleAPIView,
    AttendanceViewSet,
)

router = DefaultRouter()
router.register(r"records", AttendanceViewSet, basename="attendance-record")

urlpatterns = [
    path("", include(router.urls)),
    path("roster/", AttendanceRosterAPIView.as_view(), name="attendance-roster"),
    path("bulk/", AttendanceBulkAPIView.as_view(), name="attendance-bulk"),
    path("toggle/", AttendanceToggleAPIView.as_view(), name="attendance-toggle"),
]