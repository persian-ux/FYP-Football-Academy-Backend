from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/rbac/", include("apps.rbac.examples.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/players/", include("apps.players.urls")),
    path("api/v1/academy/", include("apps.academy.urls")),
    path("api/v1/scheduling/", include("apps.scheduling.urls")),
    path("api/v1/attendance/", include("apps.attendance.urls")),
    path("api/v1/fees/", include("apps.fees.urls")),
    path("api/v1/communications/", include("apps.communications.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    path("api/v1/ai/", include("apps.ai.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
