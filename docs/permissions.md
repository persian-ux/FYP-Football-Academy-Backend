# RBAC Permission Classes — Documentation

This document describes every reusable permission class in
`apps/rbac/permissions.py` for the **SportSphere / Football Academy** backend.

All classes rely on the existing `User.role` field defined in
`apps/accounts.models.User.Role`:

| Role     | Value   | Default access                                   |
| -------- | ------- | ------------------------------------------------ |
| Admin    | `admin` | Full access to every endpoint and resource.      |
| Coach    | `coach` | Assigned players, assigned session attendance, coaching schedules. |
| Player   | `player`| Own profile and personal resources only.         |

---

## 1. `IsAdmin`

```python
from apps.rbac.permissions import IsAdmin
```

| Attribute        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Level            | View (`has_permission`)                                   |
| Allowed roles    | `admin`                                                  |
| Denied roles     | `coach`, `player`, anonymous                              |
| HTTP result      | `403 Forbidden` for authenticated non-admins, `401` anonymous |

**When to use**

- User management (list/create/update/delete users)
- System settings and academy configuration
- Reports, analytics, integrations (admin-only)
- Any endpoint that manages *other* users' data globally.

**Example**

```python
class UserAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    queryset = User.objects.all()
```

---

## 2. `IsCoach`

```python
from apps.rbac.permissions import IsCoach
```

| Attribute        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Level            | View (`has_permission`)                                   |
| Allowed roles    | `coach`                                                  |
| Denied roles     | `admin`, `player`, anonymous                              |

**When to use**

- Coach-only panels, coaching schedules, training plans.
- Endpoints where admins intentionally should *not* act as a coach.

**Example**

```python
class CoachingScheduleView(APIView):
    permission_classes = [IsCoach]

    def get(self, request):
        ...
```

---

## 3. `IsPlayer`

```python
from apps.rbac.permissions import IsPlayer
```

| Attribute        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Level            | View (`has_permission`)                                   |
| Allowed roles    | `player`                                                 |
| Denied roles     | `admin`, `coach`, anonymous                               |

**When to use**

- Player-only endpoints (personal stats, personal achievements).
- Endpoints that should never be reached by staff.

**Example**

```python
class MyStatsAPIView(APIView):
    permission_classes = [IsPlayer]

    def get(self, request):
        ...
```

---

## 4. `IsAdminOrCoach`

```python
from apps.rbac.permissions import IsAdminOrCoach
```

| Attribute        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Level            | View (`has_permission`)                                   |
| Allowed roles    | `admin`, `coach` (staff)                                 |
| Denied roles     | `player`, anonymous                                       |

**When to use**

- Session management
- Attendance management
- Fee administration
- Any staff-facing collection endpoint where players are excluded.

**Example**

```python
class SessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrCoach]
    queryset = Session.objects.all()
```

---

## 5. `IsOwnerOrAdmin`

```python
from apps.rbac.permissions import IsOwnerOrAdmin
```

| Attribute        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Level            | Object (`has_permission` + `has_object_permission`)       |
| Access rule      | `admin` **or** the object **owner**                       |
| Denied           | Any authenticated user who is neither admin nor owner     |

**Ownership resolution** (`get_owner_user`)

The class resolves the owning `User` generically so it works for any model:

1. The object itself is a `User`
2. `obj.user` (direct FK / OneToOne)
3. `obj.owner`
4. `obj.player.user` (player profile → user)
5. `obj.coach.user` (coach profile → user)
6. Chat-style: `obj.sender` / `obj.receiver` / `obj.recipient`

**When to use**

- Player profile / personal resources
- Notifications, fees (own records), chat messages (participants)

**Example**

```python
class PlayerProfileAPIView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, pk):
        profile = get_object_or_404(PlayerProfile, pk=pk)
        self.check_object_permissions(request, profile)
        ...
```

---

## 6. `IsOwnerCoachOrAdmin`

```python
from apps.rbac.permissions import IsOwnerCoachOrAdmin
```

| Attribute        | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| Level            | Object (`has_permission` + `has_object_permission`)             |
| Access rule      | `admin` **or** owner **or** authorised coach                   |
| Denied           | Players who are not the owner, coaches without assignment       |

**Coach authorisation hooks** (on the view)

A view can define **either** hook to decide which objects a coach manages:

```python
def has_coach_object_access(self, user, obj) -> bool
```

```python
def get_coach_managed_queryset(self, user) -> QuerySet | list
```

If neither hook is defined, a coach automatically manages objects that
reference them through a `coach` FK.

**When to use**

- Attendance records (player = owner; assigned coach = manager; admin = all)
- Sessions (coach owner via `coach` FK; admin = all)
- Player records (player = owner; assigned coach = manager)

**Example**

```python
class AttendanceRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerCoachOrAdmin]
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return AttendanceRecord.objects.all()
        if user.role == "coach":
            return AttendanceRecord.objects.filter(session__coach__user=user)
        return AttendanceRecord.objects.filter(player__user=user)

    def get_coach_managed_queryset(self, user):
        return AttendanceRecord.objects.filter(session__coach__user=user)
```

---

## Global default

`config/settings.py` keeps the DRF default:

```python
"DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",)
```

Individual views/viewsets override it with the RBAC classes above.

---

## Reusability across future modules

| Module        | Suggested permission class(es)                                   |
| ------------- | ---------------------------------------------------------------- |
| Player        | `IsOwnerOrAdmin`, `IsOwnerCoachOrAdmin`, `IsAdmin`               |
| Coach         | `IsCoach`, `IsAdmin`, `IsAdminOrCoach`                           |
| Attendance    | `IsOwnerCoachOrAdmin`, `IsAdminOrCoach` (list)                   |
| Sessions      | `IsAdminOrCoach` (list), `IsOwnerCoachOrAdmin` (detail)          |
| Fees          | `IsOwnerOrAdmin`, `IsAdminOrCoach`                               |
| Notifications | `IsOwnerOrAdmin`, `IsAdmin` (broadcast)                          |
| Chat          | `IsOwnerOrAdmin` (participant check via sender/receiver)         |
| Reports       | `IsAdmin`                                                       |
| System setup  | `IsAdmin`                                                       |

