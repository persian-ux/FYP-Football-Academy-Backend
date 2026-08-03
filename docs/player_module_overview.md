# Player Management Module

## Overview

The Player module is implemented as a dedicated Django app called `players` and is separate from the authentication and RBAC concerns.

## Responsibilities

- Store a production-ready player profile linked 1:1 to the existing `accounts.User` model.
- Allow admin full create/read/update/delete access.
- Allow coaches to view assigned players and only update `performance_notes`.
- Allow players to view and update only their own profile.
- Expose pagination, searching, ordering, and filtering through the DRF API interface.
- Return standardized JSON payloads using the shared `api_response` envelope.

## Files

- `apps/players/models.py`: player profile schema linked to the auth user.
- `apps/players/serializers.py`: DRF serializers for validation and nested user creation.
- `apps/players/views.py`: ViewSet API implementation with standard response wrapping.
- `apps/players/urls.py`: router registration for `/api/v1/players/`.
- `apps/players/admin.py`: admin listing and search configuration.
- `apps/players/filters.py`: lightweight filtering utility for list endpoints.
- `apps/players/permissions.py`: role-sensitive object-level permission logic.
- `apps/players/tests.py`: regression tests for admin/coach/player flows.

## Example endpoints

- `GET /api/v1/players/`
- `POST /api/v1/players/`
- `GET /api/v1/players/{id}/`
- `PATCH /api/v1/players/{id}/`
- `DELETE /api/v1/players/{id}/`

## Response envelope

```json
{
  "success": true,
  "message": "Player retrieved successfully.",
  "data": {},
  "errors": []
}
```
