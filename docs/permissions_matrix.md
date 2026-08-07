# Permissions Matrix — Who Can Access What

This matrix defines the intended Role-Based Access Control for every module of
the SportSphere / Football Academy backend.

**Legend**

| Symbol | Meaning                         |
| ------ | ------------------------------- |
| ✅     | Full access (view/manage)       |
| 👤     | Own resources only              |
| 📋     | Assigned resources only         |
| ❌     | No access (403/404)             |

---

## 1. Example RBAC endpoints (`/api/v1/rbac/`)

| Endpoint                        | Admin | Coach | Player | Anonymous | Permission class      |
| ------------------------------- | :---: | :---: | :----: | :-------: | --------------------- |
| `GET /admin-only/`              | ✅    | ❌    | ❌     | ❌        | `IsAdmin`             |
| `GET /coach-only/`              | ❌    | ✅    | ❌     | ❌        | `IsCoach`             |
| `GET /player-only/`             | ❌    | ❌    | ✅     | ❌        | `IsPlayer`            |
| `GET /staff-only/`              | ✅    | ✅    | ❌     | ❌        | `IsAdminOrCoach`      |
| `GET /my-profile/`              | ✅    | 👤    | 👤     | ❌        | `IsOwnerOrAdmin`      |
| `GET /users/` (list)            | ✅    | ✅    | ❌     | ❌        | `IsAdminOrCoach`      |
| `GET /users/{id}/` (detail)     | ✅    | 👤    | 👤     | ❌        | `IsOwnerCoachOrAdmin` |

---

## 2. Accounts / Authentication (`/api/auth/`, `/api/v1/accounts/`)

> The Authentication module is **unchanged** by this RBAC module.

| Endpoint                | Admin | Coach | Player | Anonymous | Notes                  |
| ----------------------- | :---: | :---: | :----: | :-------: | ---------------------- |
| `POST /register/`       | —     | —     | —      | ✅        | Open registration      |
| `POST /login/`          | —     | —     | —      | ✅        | Open login             |
| `POST /refresh/`        | —     | —     | —      | ✅        | Token refresh          |
| `POST /forgot-password/`| —     | —     | —      | ✅        | Open                   |
| `POST /reset-password/` | —     | —     | —      | ✅        | Open                   |
| `GET /profile/`         | ✅    | ✅    | ✅     | ❌        | `IsAuthenticated` (own)|
| `PATCH /profile/`       | ✅    | ✅    | ✅     | ❌        | `IsAuthenticated` (own)|
| `POST /logout/`         | ✅    | ✅    | ✅     | ❌        | `IsAuthenticated`      |
| `POST /change-password/`| ✅    | ✅    | ✅     | ❌        | `IsAuthenticated` (own)|

---

## 3. Player module (future)

| Endpoint            | Admin | Coach       | Player   | Permission class      |
| ------------------- | :---: | :---------: | :------: | --------------------- |
| List players        | ✅    | 📋          | ❌       | `IsAdminOrCoach`      |
| Player detail       | ✅    | 📋          | 👤       | `IsOwnerCoachOrAdmin` |
| Create player       | ✅    | ❌          | ❌       | `IsAdmin`             |
| Update player       | ✅    | 📋          | 👤       | `IsOwnerCoachOrAdmin` |
| Delete player       | ✅    | ❌          | ❌       | `IsAdmin`             |
| Player stats        | ✅    | 📋          | 👤       | `IsOwnerCoachOrAdmin` |

---

## 4. Coach module (future)

| Endpoint           | Admin | Coach       | Player | Permission class  |
| ------------------ | :---: | :---------: | :----: | ----------------- |
| List coaches       | ✅    | ✅          | ❌     | `IsAdminOrCoach`  |
| Coach detail       | ✅    | 👤 / 📋     | ❌     | `IsOwnerOrAdmin`  |
| Create coach       | ✅    | ❌          | ❌     | `IsAdmin`         |
| Update coach       | ✅    | 👤          | ❌     | `IsOwnerOrAdmin`  |
| Delete coach       | ✅    | ❌          | ❌     | `IsAdmin`         |
| Coaching schedule  | ✅    | ✅          | ❌     | `IsAdminOrCoach`  |

---

## 5. Attendance module (future)

| Endpoint              | Admin | Coach       | Player        | Permission class      |
| --------------------- | :---: | :---------: | :-----------: | --------------------- |
| List attendance       | ✅    | 📋          | 👤            | `IsOwnerCoachOrAdmin` |
| Attendance detail     | ✅    | 📋          | 👤            | `IsOwnerCoachOrAdmin` |
| Mark attendance       | ✅    | 📋 (assigned sessions) | ❌ | `IsOwnerCoachOrAdmin` |
| Update attendance     | ✅    | 📋          | ❌            | `IsOwnerCoachOrAdmin` |
| Delete attendance     | ✅    | 📋          | ❌            | `IsOwnerCoachOrAdmin` |

---

## 6. Sessions module (future)

| Endpoint          | Admin | Coach       | Player | Permission class      |
| ----------------- | :---: | :---------: | :----: | --------------------- |
| List sessions     | ✅    | 📋          | 👤 (enrolled) | `IsOwnerCoachOrAdmin` |
| Session detail    | ✅    | 📋          | 👤 (enrolled) | `IsOwnerCoachOrAdmin` |
| Create session    | ✅    | ✅          | ❌     | `IsAdminOrCoach`      |
| Update session    | ✅    | 📋 (own)    | ❌     | `IsOwnerCoachOrAdmin` |
| Delete session    | ✅    | ❌          | ❌     | `IsAdmin`             |

---

## 7. Fees module (future)

| Endpoint         | Admin | Coach       | Player | Permission class      |
| ---------------- | :---: | :---------: | :----: | --------------------- |
| List fees        | ✅    | 📋          | 👤     | `IsOwnerCoachOrAdmin` |
| Fee detail       | ✅    | 📋          | 👤     | `IsOwnerCoachOrAdmin` |
| Create fee       | ✅    | ✅          | ❌     | `IsAdminOrCoach`      |
| Update fee       | ✅    | ❌          | ❌     | `IsAdmin`             |
| Mark as paid     | ✅    | ✅          | ❌     | `IsAdminOrCoach`      |
| Delete fee       | ✅    | ❌          | ❌     | `IsAdmin`             |

---

## 8. Notifications module (future)

| Endpoint              | Admin | Coach       | Player | Permission class  |
| --------------------- | :---: | :---------: | :----: | ----------------- |
| List own notifications| ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |
| Notification detail   | ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |
| Send broadcast        | ✅    | ❌          | ❌     | `IsAdmin`         |
| Mark read/unread      | ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |
| Delete notification   | ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |

---

## 9. Chat module (future)

| Endpoint            | Admin | Coach       | Player | Permission class  |
| ------------------- | :---: | :---------: | :----: | ----------------- |
| List conversations  | ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |
| Send message        | ✅    | 👤          | 👤     | `IsOwnerOrAdmin`  |
| Message detail      | ✅    | 👤 (party)  | 👤 (party) | `IsOwnerOrAdmin`  |
| Delete message      | ✅    | 👤 (sender) | 👤 (sender) | `IsOwnerOrAdmin`  |

---

## 10. Reports / Analytics / System (future)

| Endpoint              | Admin | Coach | Player | Permission class |
| --------------------- | :---: | :---: | :----: | ---------------- |
| Reports (all)         | ✅    | 📋 (own) | ❌  | `IsAdmin` / `IsOwnerCoachOrAdmin` |
| Analytics             | ✅    | ❌    | ❌     | `IsAdmin`        |
| System settings       | ✅    | ❌    | ❌     | `IsAdmin`        |

---

## Summary

| Permission class      | Admin | Coach | Player |
| --------------------- | :---: | :---: | :----: |
| `IsAdmin`             | ✅    | ❌    | ❌     |
| `IsCoach`             | ❌    | ✅    | ❌     |
| `IsPlayer`            | ❌    | ❌    | ✅     |
| `IsAdminOrCoach`      | ✅    | ✅    | ❌     |
| `IsOwnerOrAdmin`      | ✅    | owner | owner  |
| `IsOwnerCoachOrAdmin` | ✅    | owner or assigned | owner |

