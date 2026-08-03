# Player API Examples

## Sample request payload

```json
{
  "user": {
    "email": "player2@academy.test",
    "password": "StrongPass123!",
    "first_name": "Ali",
    "last_name": "Khan",
    "phone": "+1234567890",
    "role": "player"
  },
  "date_of_birth": "2012-05-14",
  "gender": "male",
  "emergency_contact": "+1111111111",
  "guardian_name": "Amir Khan",
  "guardian_phone": "+2222222222",
  "medical_information": "No known allergies",
  "blood_group": "O+",
  "address": "1 Academy Road",
  "assigned_sport": "Football",
  "academy_group": "U15",
  "joining_date": "2026-08-01",
  "status": "active",
  "performance_notes": "Excellent work rate"
}
```

## Sample successful response

```json
{
  "success": true,
  "message": "Player created successfully.",
  "data": {
    "id": 1,
    "user": {
      "id": 12,
      "email": "player2@academy.test",
      "first_name": "Ali",
      "last_name": "Khan",
      "phone": "+1234567890",
      "role": "player",
      "avatar": null,
      "is_active": true
    },
    "profile_photo": null,
    "date_of_birth": "2012-05-14",
    "gender": "male",
    "emergency_contact": "+1111111111",
    "guardian_name": "Amir Khan",
    "guardian_phone": "+2222222222",
    "medical_information": "No known allergies",
    "blood_group": "O+",
    "address": "1 Academy Road",
    "assigned_coach": null,
    "assigned_sport": "Football",
    "academy_group": "U15",
    "joining_date": "2026-08-01",
    "status": "active",
    "performance_notes": "Excellent work rate",
    "attendance_summary": {},
    "statistics_summary": {}
  },
  "errors": []
}
```

## Swagger exposure

Swagger/OpenAPI is available through the existing schema endpoint:

- `/api/schema/`
- `/api/docs/`

The `players` endpoint is tagged as `Players` and is discoverable in the generated schema.
