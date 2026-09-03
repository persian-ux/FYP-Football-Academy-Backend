from rest_framework.permissions import BasePermission

from apps.rbac.permissions import is_admin, is_coach


class AttendanceAccessPermission(BasePermission):
    """
    Attendance access rules:
      - Admin: full access (read + write).
    - Coach: access to their own and assigned players' records.
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
            return True

        return False