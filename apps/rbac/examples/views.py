"""
Example APIViews / ViewSets demonstrating every RBAC permission class.

These endpoints are intentionally minimal and exist so developers can:

1. See the recommended pattern for applying each permission class.
2. Test role enforcement with the provided unit tests / Postman collection.
3. Copy the pattern into future modules (Player, Coach, Attendance,
   Sessions, Fees, Notifications, Chat).
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.v1.responses import api_response
from apps.accounts.models import User
from apps.rbac.permissions import (
    IsAdmin,
    IsAdminOrCoach,
    IsCoach,
    IsOwnerCoachOrAdmin,
    IsOwnerOrAdmin,
    IsPlayer,
)

from .serializers import UserReadOnlySerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# APIView examples
# ---------------------------------------------------------------------------
class AdminOnlyAPIView(APIView):
    """Protected by :class:`apps.rbac.permissions.IsAdmin`."""

    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by("id")
        payload, status_code = api_response(
            "Admin-only: user list.",
            {"users": UserReadOnlySerializer(users, many=True).data},
            status_code=200,
        )
        return Response(payload, status=status_code)


class CoachOnlyAPIView(APIView):
    """Protected by :class:`apps.rbac.permissions.IsCoach`."""

    permission_classes = [IsCoach]

    def get(self, request):
        payload, status_code = api_response(
            "Coach-only: coaching panel.",
            {"message": "Welcome, coach!"},
            status_code=200,
        )
        return Response(payload, status=status_code)


class PlayerOnlyAPIView(APIView):
    """Protected by :class:`apps.rbac.permissions.IsPlayer`."""

    permission_classes = [IsPlayer]

    def get(self, request):
        payload, status_code = api_response(
            "Player-only: personal stats.",
            {"message": "Welcome, player!"},
            status_code=200,
        )
        return Response(payload, status=status_code)


class StaffOnlyAPIView(APIView):
    """Protected by :class:`apps.rbac.permissions.IsAdminOrCoach`."""

    permission_classes = [IsAdminOrCoach]

    def get(self, request):
        payload, status_code = api_response(
            "Staff-only: admin or coach.",
            {"message": "Welcome, staff!"},
            status_code=200,
        )
        return Response(payload, status=status_code)


class MyProfileAPIView(APIView):
    """
    Protected by :class:`apps.rbac.permissions.IsOwnerOrAdmin`.

    Any authenticated user can GET their own profile; admins may view any
    profile by passing ``?user_id=``.
    """

    permission_classes = [IsOwnerOrAdmin]

    def get(self, request):
        user_id = request.query_params.get("user_id")
        if user_id is not None:
            # Admin-only path: raise 404 for non-admins via object check.
            try:
                target = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                payload, status_code = api_response(
                    "User not found.",
                    success=False,
                    status_code=404,
                )
                return Response(payload, status=status_code)
            self.check_object_permissions(request, target)
            user = target
        else:
            user = request.user

        payload, status_code = api_response(
            "Profile retrieved.",
            {"user": UserReadOnlySerializer(user).data},
            status_code=200,
        )
        return Response(payload, status=status_code)


# ---------------------------------------------------------------------------
# ViewSet example
# ---------------------------------------------------------------------------
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet protected by object-level RBAC.

    * ``admin``  -> sees every user.
    * ``coach``  -> sees themselves (via the coach hook).
    * ``player`` -> sees only their own record.

    Demonstrates:
      * per-action permissions via :meth:`get_permissions`
      * the ``get_coach_managed_queryset`` hook used by
        :class:`apps.rbac.permissions.IsOwnerCoachOrAdmin`
    """

    serializer_class = UserReadOnlySerializer
    permission_classes = [IsOwnerCoachOrAdmin]

    def get_queryset(self):  # type: ignore[override]
        return User.objects.all().order_by("id")

    def get_permissions(self):
        if self.action == "list":
            # Listing requires staff privileges.
            return [permission() for permission in [IsAdminOrCoach]]
        return super().get_permissions()

    def get_coach_managed_queryset(self, user):
        # A coach only manages their own profile here (no assignments yet).
        return User.objects.filter(pk=user.pk)

