"""
Unit and integration tests for the Role-Based Authorization (RBAC) module.

Coverage
--------
* Helper functions: ``is_admin``, ``is_coach``, ``is_player``,
  ``get_owner_user``, ``user_has_ownership``.
* View-level permission classes:
  :class:`IsAdmin`, :class:`IsCoach`, :class:`IsPlayer`, :class:`IsAdminOrCoach`.
* Object-level permission classes:
  :class:`IsOwnerOrAdmin`, :class:`IsOwnerCoachOrAdmin` (incl. coach hooks).
* API integration tests against the example views and ViewSet.
"""

import json

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.rbac.permissions import (
    IsAdmin,
    IsAdminOrCoach,
    IsCoach,
    IsOwnerCoachOrAdmin,
    IsOwnerOrAdmin,
    IsPlayer,
    get_owner_user,
    is_admin,
    is_coach,
    is_player,
    user_has_ownership,
)

User = get_user_model()


def make_user(email, role="player", **kwargs):
    user = User.objects.create_user(email=email, password="StrongPass123!", role=role, **kwargs)
    return user


class FakeObject:
    """Stand-in model object with various ownership relations."""

    def __init__(self, **kwargs):
        self.pk = kwargs.pop("pk", 1)
        for key, value in kwargs.items():
            setattr(self, key, value)


class RoleHelpersTests(TestCase):
    """Tests for the small role helper functions."""

    def setUp(self):
        self.admin = make_user("admin@test.com", role="admin")
        self.coach = make_user("coach@test.com", role="coach")
        self.player = make_user("player@test.com", role="player")

    def test_is_admin(self):
        self.assertTrue(is_admin(self.admin))
        self.assertFalse(is_admin(self.coach))
        self.assertFalse(is_admin(self.player))
        self.assertFalse(is_admin(None))

    def test_is_coach(self):
        self.assertTrue(is_coach(self.coach))
        self.assertFalse(is_coach(self.admin))
        self.assertFalse(is_coach(self.player))

    def test_is_player(self):
        self.assertTrue(is_player(self.player))
        self.assertFalse(is_player(self.admin))
        self.assertFalse(is_player(self.coach))


class OwnerResolutionTests(TestCase):
    """Tests for generic owner resolution used by object-level classes."""

    def setUp(self):
        self.owner = make_user("owner@test.com", role="player")
        self.other = make_user("other@test.com", role="player")

    def test_user_object_itself_is_owner(self):
        self.assertEqual(get_owner_user(self.owner), self.owner)

    def test_direct_user_fk(self):
        obj = FakeObject(user=self.owner)
        self.assertEqual(get_owner_user(obj), self.owner)
        self.assertTrue(user_has_ownership(self.owner, obj))
        self.assertFalse(user_has_ownership(self.other, obj))

    def test_player_nested_user(self):
        player = FakeObject(user=self.owner)
        obj = FakeObject(player=player)
        self.assertEqual(get_owner_user(obj), self.owner)
        self.assertTrue(user_has_ownership(self.owner, obj))

    def test_coach_nested_user(self):
        coach = FakeObject(user=self.owner)
        obj = FakeObject(coach=coach)
        self.assertEqual(get_owner_user(obj), self.owner)

    def test_chat_sender_receiver(self):
        obj = FakeObject(sender=self.owner, receiver=self.other)
        self.assertTrue(user_has_ownership(self.owner, obj))
        self.assertTrue(user_has_ownership(self.other, obj))

    def test_no_owner(self):
        obj = FakeObject(title="no relation")
        self.assertIsNone(get_owner_user(obj))
        self.assertFalse(user_has_ownership(self.owner, obj))


class PermissionRequest:
    """Minimal request wrapper exposing a ``user`` attribute."""

    def __init__(self, user):
        self.user = user


class ViewLevelPermissionTests(TestCase):
    """Tests for IsAdmin, IsCoach, IsPlayer, IsAdminOrCoach."""

    def setUp(self):
        self.admin = make_user("admin@test.com", role="admin")
        self.coach = make_user("coach@test.com", role="coach")
        self.player = make_user("player@test.com", role="player")
        self.view = APIView()

    def _check(self, permission_cls, user):
        return permission_cls().has_permission(PermissionRequest(user), self.view)

    def test_is_admin(self):
        self.assertTrue(self._check(IsAdmin, self.admin))
        self.assertFalse(self._check(IsAdmin, self.coach))
        self.assertFalse(self._check(IsAdmin, self.player))
        self.assertFalse(self._check(IsAdmin, None))

    def test_is_coach(self):
        self.assertTrue(self._check(IsCoach, self.coach))
        self.assertFalse(self._check(IsCoach, self.admin))
        self.assertFalse(self._check(IsCoach, self.player))

    def test_is_player(self):
        self.assertTrue(self._check(IsPlayer, self.player))
        self.assertFalse(self._check(IsPlayer, self.admin))
        self.assertFalse(self._check(IsPlayer, self.coach))

    def test_is_admin_or_coach(self):
        self.assertTrue(self._check(IsAdminOrCoach, self.admin))
        self.assertTrue(self._check(IsAdminOrCoach, self.coach))
        self.assertFalse(self._check(IsAdminOrCoach, self.player))
        self.assertFalse(self._check(IsAdminOrCoach, None))


class ObjectLevelPermissionTests(TestCase):
    """Tests for IsOwnerOrAdmin and IsOwnerCoachOrAdmin."""

    def setUp(self):
        self.admin = make_user("admin@test.com", role="admin")
        self.coach = make_user("coach@test.com", role="coach")
        self.owner = make_user("owner@test.com", role="player")
        self.other = make_user("other@test.com", role="player")
        self.view = APIView()

    def test_is_owner_or_admin_admin_ok(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerOrAdmin()
        self.assertTrue(perm.has_permission(PermissionRequest(self.admin), self.view))
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.admin), self.view, obj))

    def test_is_owner_or_admin_owner_ok(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.owner), self.view, obj))

    def test_is_owner_or_admin_other_denied(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerOrAdmin()
        self.assertFalse(perm.has_object_permission(PermissionRequest(self.other), self.view, obj))
        self.assertFalse(perm.has_object_permission(PermissionRequest(self.coach), self.view, obj))

    def test_is_owner_or_admin_anonymous_denied(self):
        perm = IsOwnerOrAdmin()
        self.assertFalse(perm.has_permission(PermissionRequest(None), self.view))

    def test_is_owner_coach_or_admin_admin_ok(self):
        obj = FakeObject(user=self.owner, coach=FakeObject(user=self.coach))
        perm = IsOwnerCoachOrAdmin()
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.admin), self.view, obj))

    def test_is_owner_coach_or_admin_owner_ok(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerCoachOrAdmin()
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.owner), self.view, obj))

    def test_coach_with_own_coach_fk_ok(self):
        coach_profile = FakeObject(user=self.coach)
        obj = FakeObject(coach=coach_profile)
        perm = IsOwnerCoachOrAdmin()
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.coach), self.view, obj))

    def test_coach_with_view_hook(self):
        class CoachView(APIView):
            def has_coach_object_access(self, user, obj):
                return obj.coach.user == user

        obj = FakeObject(user=self.owner, coach=FakeObject(user=self.coach))
        perm = IsOwnerCoachOrAdmin()
        view = CoachView()
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.coach), view, obj))
        # A different coach is not allowed.
        other_coach = make_user("othercoach@test.com", role="coach")
        self.assertFalse(perm.has_object_permission(PermissionRequest(other_coach), view, obj))

    def test_coach_with_managed_queryset(self):
        class CoachView(APIView):
            allowed = set()

            def get_coach_managed_queryset(self, user):
                return FakeObject if False else [obj for obj in self.allowed if obj.coach.user == user]

        obj = FakeObject(user=self.owner, coach=FakeObject(user=self.coach), pk=42)
        other = FakeObject(user=self.owner, coach=FakeObject(user=self.other), pk=43)

        perm = IsOwnerCoachOrAdmin()

        CoachView.allowed = {obj}
        self.assertTrue(perm.has_object_permission(PermissionRequest(self.coach), CoachView(), obj))
        self.assertFalse(perm.has_object_permission(PermissionRequest(self.coach), CoachView(), other))

    def test_coach_unrelated_denied(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerCoachOrAdmin()
        self.assertFalse(perm.has_object_permission(PermissionRequest(self.coach), self.view, obj))

    def test_player_other_denied(self):
        obj = FakeObject(user=self.owner)
        perm = IsOwnerCoachOrAdmin()
        self.assertFalse(perm.has_object_permission(PermissionRequest(self.other), self.view, obj))


class RBACAPIViewIntegrationTests(APITestCase):
    """End-to-end tests against the example RBAC endpoints."""

    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user("admin@example.com", role="admin")
        cls.coach = make_user("coach@example.com", role="coach")
        cls.player = make_user("player@example.com", role="player")
        cls.other_player = make_user("other@example.com", role="player")

    def _auth(self, user):
        self.client.force_authenticate(user=user)  # type: ignore[attr-defined]

    # --- IsAdmin ---------------------------------------------------------
    def test_admin_only_admin_allowed(self):
        self._auth(self.admin)
        response = self.client.get("/api/v1/rbac/admin-only/")
        self.assertEqual(response.status_code, 200)

    def test_admin_only_coach_denied(self):
        self._auth(self.coach)
        response = self.client.get("/api/v1/rbac/admin-only/")
        self.assertEqual(response.status_code, 403)

    def test_admin_only_player_denied(self):
        self._auth(self.player)
        response = self.client.get("/api/v1/rbac/admin-only/")
        self.assertEqual(response.status_code, 403)

    # --- IsCoach ---------------------------------------------------------
    def test_coach_only_coach_allowed(self):
        self._auth(self.coach)
        response = self.client.get("/api/v1/rbac/coach-only/")
        self.assertEqual(response.status_code, 200)

    def test_coach_only_admin_denied(self):
        self._auth(self.admin)
        response = self.client.get("/api/v1/rbac/coach-only/")
        self.assertEqual(response.status_code, 403)

    # --- IsPlayer --------------------------------------------------------
    def test_player_only_player_allowed(self):
        self._auth(self.player)
        response = self.client.get("/api/v1/rbac/player-only/")
        self.assertEqual(response.status_code, 200)

    def test_player_only_coach_denied(self):
        self._auth(self.coach)
        response = self.client.get("/api/v1/rbac/player-only/")
        self.assertEqual(response.status_code, 403)

    # --- IsAdminOrCoach --------------------------------------------------
    def test_staff_only_admin_allowed(self):
        self._auth(self.admin)
        response = self.client.get("/api/v1/rbac/staff-only/")
        self.assertEqual(response.status_code, 200)

    def test_staff_only_coach_allowed(self):
        self._auth(self.coach)
        response = self.client.get("/api/v1/rbac/staff-only/")
        self.assertEqual(response.status_code, 200)

    def test_staff_only_player_denied(self):
        self._auth(self.player)
        response = self.client.get("/api/v1/rbac/staff-only/")
        self.assertEqual(response.status_code, 403)

    # --- IsOwnerOrAdmin --------------------------------------------------
    def test_my_profile_own(self):
        self._auth(self.player)
        response = self.client.get("/api/v1/rbac/my-profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["user"]["id"], self.player.pk)

    def test_my_profile_other_player_via_user_id(self):
        self._auth(self.player)
        other_player_id = self.other_player.pk
        response = self.client.get(f"/api/v1/rbac/my-profile/?user_id={other_player_id}")
        self.assertEqual(response.status_code, 403)

    def test_my_profile_admin_can_view_any(self):
        self._auth(self.admin)
        other_player_id = self.other_player.pk
        response = self.client.get(f"/api/v1/rbac/my-profile/?user_id={other_player_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["user"]["id"], self.other_player.pk)

    # --- IsOwnerCoachOrAdmin (ViewSet) -----------------------------------
    def test_viewset_list_admin(self):
        self._auth(self.admin)
        response = self.client.get("/api/v1/rbac/users/")
        self.assertEqual(response.status_code, 200)

    def test_viewset_list_coach(self):
        self._auth(self.coach)
        response = self.client.get("/api/v1/rbac/users/")
        self.assertEqual(response.status_code, 200)

    def test_viewset_list_player_denied(self):
        self._auth(self.player)
        response = self.client.get("/api/v1/rbac/users/")
        self.assertEqual(response.status_code, 403)

    def test_viewset_detail_owner_ok(self):
        self._auth(self.player)
        response = self.client.get(f"/api/v1/rbac/users/{self.player.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_viewset_detail_other_player_denied(self):
        self._auth(self.player)
        response = self.client.get(f"/api/v1/rbac/users/{self.other_player.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_viewset_detail_admin_ok(self):
        self._auth(self.admin)
        response = self.client.get(f"/api/v1/rbac/users/{self.other_player.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_viewset_detail_coach_own_ok(self):
        self._auth(self.coach)
        response = self.client.get(f"/api/v1/rbac/users/{self.coach.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_denied(self):
        response = self.client.get("/api/v1/rbac/admin-only/")
        self.assertEqual(response.status_code, 401)


class SchemaTests(APITestCase):
    """Swagger/OpenAPI schema is generated and reachable."""

    def test_schema_endpoint(self):
        # The test client uses HTTP_HOST=testserver; ALLOWED_HOSTS does not
        # include it, so pass an allowed host explicitly.
        # Request JSON format explicitly (drf-spectacular defaults to YAML).
        response = self.client.get("/api/schema/?format=json", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        # drf-spectacular returns OpenAPI with a vendor content-type
        # (application/vnd.oai.openapi), so parse content directly.
        schema = json.loads(response.content)
        self.assertEqual(schema["info"]["title"], "SportSphere / Football Academy API")
        self.assertEqual(schema["openapi"].split(".")[0], "3")

    def test_swagger_ui_redirects_or_renders(self):
        response = self.client.get("/api/docs/", HTTP_HOST="localhost")
        self.assertIn(response.status_code, (200, 302))

