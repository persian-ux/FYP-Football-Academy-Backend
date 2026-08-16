from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MatchViewSet, TeamViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"matches", MatchViewSet, basename="match")

urlpatterns = [
    path("", include(router.urls)),
]