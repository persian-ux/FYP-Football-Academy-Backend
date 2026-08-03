"""
Role-Based Access Control (RBAC) — Reusable DRF Permission Classes
===================================================================

This module provides drop-in permission classes for Django REST Framework
that enforce the SportSphere role model defined on ``apps.accounts.User.role``:

    * ``admin``  — full access to every API endpoint.
    * ``coach``  — manages assigned players, attendance and coaching schedules.
    * ``player`` — can only access their own profile and personal resources.

Classes
-------
* :class:`IsAdmin`             — only ``admin`` users.
* :class:`IsCoach`             — only ``coach`` users.
* :class:`IsPlayer`            — only ``player`` users.
* :class:`IsAdminOrCoach`      — ``admin`` or ``coach`` users (staff).
* :class:`IsOwnerOrAdmin`      — ``admin`` or the owner of the target object.
* :class:`IsOwnerCoachOrAdmin` — ``admin``, the owner, or an authorised coach.

Reusability
-----------
The object-level permission classes resolve the "owner" generically so they
work with any model (Player, Coach, Attendance, Sessions, Fees, Notifications,
Chat, ...) without modification:

* an object with a ``user`` FK / OneToOne  (Notification, Profile, ...)
* an object with an ``owner`` FK
* an object with a ``player`` FK           (resolved via ``player.user``)
* an object with a ``coach`` FK            (resolved via ``coach.user``)
* chat-style objects with ``sender`` / ``receiver`` FKs
* the ``accounts.User`` model itself

Custom coach rules (e.g. "a coach may only manage *assigned* players") are
supported through optional view hooks:

* ``view.has_coach_object_access(user, obj) -> bool``
* ``view.get_coach_managed_queryset(user) -> QuerySet | list``

If neither hook is defined, a coach automatically manages objects that
reference them through a ``coach`` FK.
"""

from typing import Any, cast

from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

User = get_user_model()

# ---------------------------------------------------------------------------
# Role constants (mirror apps.accounts.models.User.Role)
# ---------------------------------------------------------------------------
ROLE_ADMIN = "admin"
ROLE_COACH = "coach"
ROLE_PLAYER = "player"

STAFF_ROLES = (ROLE_ADMIN, ROLE_COACH)  # admin + coach

__all__ = [
    "ROLE_ADMIN",
    "ROLE_COACH",
    "ROLE_PLAYER",
    "STAFF_ROLES",
    "is_admin",
    "is_coach",
    "is_player",
    "get_owner_user",
    "user_has_ownership",
    "IsAdmin",
    "IsCoach",
    "IsPlayer",
    "IsAdminOrCoach",
    "IsOwnerOrAdmin",
    "IsOwnerCoachOrAdmin",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_authenticated(user):
    return bool(user and user.is_authenticated)


def is_admin(user):
    """Return ``True`` when ``user`` has the ``admin`` role."""
    return _is_authenticated(user) and getattr(user, "role", None) == ROLE_ADMIN


def is_coach(user):
    """Return ``True`` when ``user`` has the ``coach`` role."""
    return _is_authenticated(user) and getattr(user, "role", None) == ROLE_COACH


def is_player(user):
    """Return ``True`` when ``user`` has the ``player`` role."""
    return _is_authenticated(user) and getattr(user, "role", None) == ROLE_PLAYER


def get_owner_user(obj):
    """
    Resolve the owning ``User`` from any model instance.

    Lookup order:

    1. the object itself is a ``User``
    2. ``obj.user``               (direct FK / OneToOne)
    3. ``obj.owner``              (generic owner FK)
    4. ``obj.player.user``        (player profile -> user)
    5. ``obj.coach.user``         (coach profile -> user)
    6. chat-style ``sender`` / ``receiver`` / ``recipient`` FKs

    Returns ``None`` when no owner can be determined.
    """
    if obj is None:
        return None
    if isinstance(obj, User):
        return obj

    for attr in ("user", "owner"):
        candidate = getattr(obj, attr, None)
        if isinstance(candidate, User):
            return candidate

    for attr in ("player", "coach"):
        candidate = getattr(obj, attr, None)
        if candidate is None:
            continue
        if isinstance(candidate, User):
            return candidate
        nested = getattr(candidate, "user", None)
        if isinstance(nested, User):
            return nested

    # Chat / messaging models
    for attr in ("sender", "receiver", "recipient", "from_user", "to_user"):
        candidate = getattr(obj, attr, None)
        if isinstance(candidate, User):
            return candidate

    return None


def user_has_ownership(user, obj):
    """
    Return ``True`` when ``user`` owns ``obj``.

    In addition to :func:`get_owner_user`, conversation-style objects are
    considered owned when the user is *either* party (sender or receiver).
    """
    if not _is_authenticated(user):
        return False

    owner = get_owner_user(obj)
    if owner is not None and owner.pk == user.pk:
        return True

    for attr in ("sender", "receiver", "recipient", "from_user", "to_user"):
        candidate = getattr(obj, attr, None)
        if candidate is None:
            continue
        if isinstance(candidate, User) and candidate.pk == user.pk:
            return True
        nested = getattr(candidate, "user", None)
        if isinstance(nested, User) and nested.pk == user.pk:
            return True

    return False


def _coach_has_object_access(user, view, obj):
    """
    Resolve whether a coach may access ``obj``.

    1. ``view.has_coach_object_access(user, obj)`` hook (recommended)
    2. ``view.get_coach_managed_queryset(user)`` hook (queryset/list)
    3. default: the object references this coach via a ``coach`` FK
    """
    accessor = getattr(view, "has_coach_object_access", None)
    if callable(accessor):
        try:
            return bool(accessor(user, obj))
        except TypeError:
            return False

    manager = getattr(view, "get_coach_managed_queryset", None)
    if callable(manager):
        try:
            managed = manager(user)
        except TypeError:
            return False
        if managed is None:
            return False

        managed_any: Any = managed
        if hasattr(managed_any, "filter"):
            queryset = cast(Any, managed_any)
            return bool(queryset.filter(pk=obj.pk).exists())
        return any(getattr(item, "pk", None) == obj.pk for item in managed_any)

    coach = getattr(obj, "coach", None)
    if coach is not None:
        coach_user = getattr(coach, "user", None) or coach
        if isinstance(coach_user, User) and coach_user.pk == user.pk:
            return True

    return False


# ---------------------------------------------------------------------------
# View-level (collection) permission classes
# ---------------------------------------------------------------------------
class IsAdmin(BasePermission):
    """
    Grants access only to users with the ``admin`` role.

    Use on admin-only endpoints such as user management, system settings,
    reports, analytics and academy-wide configuration.

    Example::

        class AdminOnlyView(APIView):
            permission_classes = [IsAdmin]
    """

    message = "Admin privileges are required to access this endpoint."

    def has_permission(self, request, view):  # type: ignore[override]
        return bool(is_admin(request.user))


class IsCoach(BasePermission):
    """
    Grants access only to users with the ``coach`` role.

    Use on coach-only endpoints such as managing assigned players,
    coaching schedules and session attendance.

    Example::

        class CoachOnlyView(APIView):
            permission_classes = [IsCoach]
    """

    message = "Coach privileges are required to access this endpoint."

    def has_permission(self, request, view):  # type: ignore[override]
        return bool(is_coach(request.user))


class IsPlayer(BasePermission):
    """
    Grants access only to users with the ``player`` role.

    Use on player-only endpoints such as personal stats and own resources.

    Example::

        class PlayerOnlyView(APIView):
            permission_classes = [IsPlayer]
    """

    message = "Player privileges are required to access this endpoint."

    def has_permission(self, request, view):  # type: ignore[override]
        return bool(is_player(request.user))


class IsAdminOrCoach(BasePermission):
    """
    Grants access to users with the ``admin`` **or** ``coach`` role.

    Use on staff-facing endpoints such as session management, attendance
    management and fee administration where players should be excluded.

    Example::

        class SessionManagementViewSet(ModelViewSet):
            permission_classes = [IsAdminOrCoach]
    """

    message = "Admin or coach privileges are required to access this endpoint."

    def has_permission(self, request, view):  # type: ignore[override]
        return bool(
            _is_authenticated(request.user)
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


# ---------------------------------------------------------------------------
# Object-level permission classes
# ---------------------------------------------------------------------------
class IsOwnerOrAdmin(BasePermission):
    """
    Grants access when the user is:

    * an ``admin`` (full access), **or**
    * the **owner** of the target object.

    Ownership is resolved generically via :func:`get_owner_user`, so the class
    works unchanged for User, Player, Coach, Attendance, Fees, Notifications,
    Chat and any future model that exposes a ``user`` / ``owner`` / ``player``
    / ``coach`` / ``sender`` / ``receiver`` relation.

    Example::

        class PlayerProfileView(APIView):
            permission_classes = [IsOwnerOrAdmin]

            def get(self, request, pk):
                player = get_object_or_404(PlayerProfile, pk=pk)
                self.check_object_permissions(request, player)
                ...
    """

    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):  # type: ignore[override]
        # Authenticated users may reach the endpoint (e.g. to retrieve their
        # own record from a list). Fine-grained checks happen on the object.
        return bool(_is_authenticated(request.user))

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        user = request.user
        if is_admin(user):
            return True
        return bool(user_has_ownership(user, obj))


class IsOwnerCoachOrAdmin(BasePermission):
    """
    Grants access when the user is:

    * an ``admin`` (full access), **or**
    * the **owner** of the target object, **or**
    * a **coach** authorised to manage the object (own objects, or objects
      assigned to them via the view hooks ``has_coach_object_access`` or
      ``get_coach_managed_queryset``).

    This is the most flexible class and is intended for resources that both
    players and coaches interact with (attendance, sessions, player records).

    Example::

        class AttendanceRecordViewSet(ModelViewSet):
            permission_classes = [IsOwnerCoachOrAdmin]

            def get_coach_managed_queryset(self, user):
                # In a real module, return only sessions assigned to ``user``.
                return AttendanceRecord.objects.filter(
                    session__coach__user=user
                )
    """

    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):  # type: ignore[override]
        return bool(_is_authenticated(request.user))

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
        user = request.user
        if is_admin(user):
            return True
        if user_has_ownership(user, obj):
            return True
        if is_coach(user):
            return bool(_coach_has_object_access(user, view, obj))
        return False

