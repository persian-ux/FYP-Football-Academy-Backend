from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.rbac.permissions import is_admin, is_coach, is_player


class PlayerAccessPermission(BasePermission):
    message = "You do not have permission to perform this action on the player profile."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if is_admin(user):
            return True

        if is_player(user):
            return obj.user_id == user.pk

        if is_coach(user):
            if request.method in SAFE_METHODS:
                return obj.assigned_coach_id == user.pk

            if request.method in {"PATCH", "PUT"}:
                allowed_fields = {"performance_notes"}
                requested_fields = set(request.data.keys())
                return obj.assigned_coach_id == user.pk and requested_fields.issubset(allowed_fields)

        return False
