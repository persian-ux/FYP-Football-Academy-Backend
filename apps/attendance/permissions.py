from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.rbac.permissions import is_admin, is_coach


class AttendanceAccessPermission(BasePermission):
    """
    Attendance access rules:
      - Admin: full access (read + write).
      - Coach: read-only access to attendance records.
      - Player: no access to the attendance management endpoints.
    """

    message = "You do not have permission to manage attendance."

    def has_permission(self, request, view):  # type: ignore[override]
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if is_admin(user):
            return True

        if is_coach(user):
            return request.method in SAFE_METHODS

        return False