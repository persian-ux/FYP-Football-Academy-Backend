from datetime import date as date_cls

from django.db import transaction
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.v1.responses import api_response
from apps.accounts.models import User
from apps.rbac.permissions import IsAdmin, IsAdminOrCoach, is_coach

from .models import AttendanceRecord
from .permissions import AttendanceAccessPermission
from .serializers import (
    ATTENDANCE_ROLES,
    AttendanceBulkSerializer,
    AttendanceRosterItemSerializer,
    AttendanceSerializer,
    AttendanceToggleSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Attendance"], summary="List attendance records"),
    retrieve=extend_schema(tags=["Attendance"], summary="Retrieve attendance record"),
    create=extend_schema(tags=["Attendance"], summary="Create attendance record"),
    update=extend_schema(tags=["Attendance"], summary="Update attendance record"),
    partial_update=extend_schema(tags=["Attendance"], summary="Update attendance record partially"),
    destroy=extend_schema(tags=["Attendance"], summary="Delete attendance record"),
)
class AttendanceViewSet(viewsets.ModelViewSet):
    """CRUD operations for attendance records shared by admins and coaches."""

    queryset = AttendanceRecord.objects.select_related("user", "marked_by").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, AttendanceAccessPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "status",
    ]
    ordering_fields = ["id", "date", "status", "created_at", "updated_at"]
    ordering = ["-date", "-id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if is_coach(self.request.user):
            queryset = queryset.filter(
                models.Q(user=self.request.user)
                | models.Q(user__player_profile__assigned_coach=self.request.user)
            )

        # Filter by date: ?date=YYYY-MM-DD
        date_param = self.request.query_params.get("date")
        if date_param:
            queryset = queryset.filter(date=date_param)

        # Filter by role: ?role=player or ?role=coach
        role = self.request.query_params.get("role")
        if role in ATTENDANCE_ROLES:
            queryset = queryset.filter(user__role=role)

        # Filter by status: ?status=present|absent|late|excused
        status_param = self.request.query_params.get("status")
        if status_param in AttendanceRecord.Status.values:
            queryset = queryset.filter(status=status_param)

        return queryset

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminOrCoach()]
        return [IsAuthenticated(), AttendanceAccessPermission()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Attendance record created successfully.",
                AttendanceSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Attendance record creation failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        payload, status_code = api_response(
            "Attendance records retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response(
            "Attendance record retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response(
                "Attendance record updated successfully.",
                serializer.data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Attendance record update failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        payload, status_code = api_response(
            "Attendance record deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        return Response(payload, status=status_code)


@extend_schema(
    tags=["Attendance"],
    summary="Load attendance roster",
    description=(
        "Load all players and coaches with their attendance status for a given date. "
        "Admin only. Use ?date=YYYY-MM-DD (defaults to today)."
    ),
)
class AttendanceRosterAPIView(APIView):
    """Load all students (players) and coaches to mark their attendance."""

    permission_classes = [IsAdminOrCoach]

    def get(self, request, *args, **kwargs):
        date_param = request.query_params.get("date")
        try:
            target_date = date_cls.fromisoformat(date_param) if date_param else date_cls.today()
        except ValueError:
            payload, status_code = api_response(
                "Invalid date format. Use YYYY-MM-DD.",
                errors={"date": ["Invalid date format. Use YYYY-MM-DD."]},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        users = User.objects.filter(role__in=ATTENDANCE_ROLES, is_active=True)
        if is_coach(request.user):
            users = users.filter(
                models.Q(pk=request.user.pk)
                | models.Q(player_profile__assigned_coach=request.user)
            )
        users = users.order_by(
            "role", "first_name", "last_name"
        )

        # Fetch existing attendance records for the date in one query
        records = {
            record.user_id: record  # type: ignore[attr-defined]
            for record in AttendanceRecord.objects.filter(date=target_date, user__in=users)
        }

        roster = []
        for user in users:
            record = records.get(user.id)  # type: ignore[attr-defined]
            roster.append(
                {
                    "user_id": user.id,  # type: ignore[attr-defined]
                    "name": user.get_full_name() or user.email,
                    "email": user.email,
                    "role": user.role,
                    "status": record.status if record else AttendanceRecord.Status.ABSENT,
                    "attendance_id": record.id if record else None,  # type: ignore[attr-defined]
                }
            )

        serializer = AttendanceRosterItemSerializer(roster, many=True)
        payload, status_code = api_response(
            "Attendance roster retrieved successfully.",
            {"date": target_date.isoformat(), "count": len(roster), "roster": serializer.data},
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


@extend_schema(
    tags=["Attendance"],
    summary="Bulk mark attendance",
    description=(
        "Mark attendance for multiple players/coaches on a single date. "
        "Existing records for the same user+date are updated. Admin only."
    ),
    request=AttendanceBulkSerializer,
)
class AttendanceBulkAPIView(APIView):
    """Bulk create/update attendance for multiple users on a single date."""

    permission_classes = [IsAdminOrCoach]

    def post(self, request, *args, **kwargs):
        serializer = AttendanceBulkSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            payload, status_code = api_response(
                "Bulk attendance failed.",
                errors=serializer.errors,
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        data = serializer.validated_data  # type: ignore[assignment]
        target_date = data["date"]  # type: ignore[index]
        records = data["records"]  # type: ignore[index]

        created = []
        updated = []
        with transaction.atomic():
            for item in records:
                user = item["user"]
                status_value = item["status"]
                record, was_created = AttendanceRecord.objects.update_or_create(
                    user=user,
                    date=target_date,
                    defaults={
                        "status": status_value,
                        "marked_by": request.user,
                    },
                )
                (created if was_created else updated).append(record)

        payload, status_code = api_response(
            "Bulk attendance marked successfully.",
            {
                "date": target_date.isoformat(),
                "created": len(created),
                "updated": len(updated),
                "total": len(created) + len(updated),
            },
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


@extend_schema(
    tags=["Attendance"],
    summary="Toggle attendance status",
    description=(
        "Toggle a single user's attendance between present and absent for a given date. "
        "If no record exists it is created as present. Admin only."
    ),
    request=AttendanceToggleSerializer,
)
class AttendanceToggleAPIView(APIView):
    """Toggle a user's attendance between present and absent."""

    permission_classes = [IsAdminOrCoach]

    def post(self, request, *args, **kwargs):
        serializer = AttendanceToggleSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            payload, status_code = api_response(
                "Attendance toggle failed.",
                errors=serializer.errors,
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        data = serializer.validated_data  # type: ignore[assignment]
        user = data["user"]  # type: ignore[index]
        target_date = data["date"]  # type: ignore[index]

        record, created = AttendanceRecord.objects.get_or_create(
            user=user,
            date=target_date,
            defaults={"status": AttendanceRecord.Status.PRESENT, "marked_by": request.user},
        )

        if not created:
            # Toggle between present and absent
            new_status = (
                AttendanceRecord.Status.ABSENT
                if record.status == AttendanceRecord.Status.PRESENT
                else AttendanceRecord.Status.PRESENT
            )
            record.status = new_status
            record.marked_by = request.user
            record.save()

        payload, status_code = api_response(
            "Attendance toggled successfully.",
            AttendanceSerializer(record, context={"request": request}).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)