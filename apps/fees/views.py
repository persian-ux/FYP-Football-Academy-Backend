from decimal import Decimal

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from apps.players.models import Player
from apps.rbac.permissions import IsAdmin
from .models import FeeRecord
from .serializers import FeeRecordSerializer


@extend_schema_view(
    list=extend_schema(tags=["Fees"], summary="List fee records"),
    retrieve=extend_schema(tags=["Fees"], summary="Get fee record"),
    create=extend_schema(tags=["Fees"], summary="Create fee record"),
    update=extend_schema(tags=["Fees"], summary="Update fee record"),
    partial_update=extend_schema(tags=["Fees"], summary="Update fee record partially"),
    destroy=extend_schema(tags=["Fees"], summary="Delete fee record"),
)
class FeeRecordViewSet(viewsets.ModelViewSet):
    queryset = FeeRecord.objects.select_related("player__user").all()
    serializer_class = FeeRecordSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "player__user__email",
        "player__user__first_name",
        "player__user__last_name",
        "status",
    ]
    ordering_fields = ["id", "amount", "status", "due_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            return queryset
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Fee record created successfully.",
                FeeRecordSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Fee record creation failed.",
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
            "Fee records retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Fee record retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response("Fee record updated successfully.", serializer.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Fee record update failed.",
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
        payload, status_code = api_response("Fee record deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)

    @action(detail=False, methods=["get"], url_path="students")
    def students(self, request, *args, **kwargs):
        queryset = Player.objects.select_related("user").order_by("-id")
        students = []
        for player in queryset:
            fee_record = player.fee_records.order_by("-created_at").first() if hasattr(player, "fee_records") else None
            students.append(
                {
                    "id": player.pk,
                    "player_id": player.pk,
                    "user_id": player.user_id,
                    "student_name": player.user.get_full_name() or player.user.email,
                    "email": player.user.email,
                    "phone": player.user.phone,
                    "academy_group": player.academy_group,
                    "assigned_sport": player.assigned_sport,
                    "amount": str(fee_record.amount) if fee_record else "0.00",
                    "status": fee_record.status if fee_record else FeeRecord.Status.UNPAID,
                    "fee_id": fee_record.pk if fee_record else None,
                    "due_date": fee_record.due_date.isoformat() if fee_record and fee_record.due_date else None,
                }
            )
        payload, status_code = api_response("Students with fee status retrieved successfully.", students, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    @action(detail=True, methods=["patch"], url_path="toggle-status")
    def toggle_status(self, request, *args, **kwargs):
        instance = self.get_object()
        status_value = request.data.get("status")
        if status_value is not None:
            normalized = str(status_value).strip().lower()
            if normalized in {"pending", "unpaid"}:
                instance.status = FeeRecord.Status.UNPAID
            elif normalized in {"paid"}:
                instance.status = FeeRecord.Status.PAID
            elif normalized in {"overdue"}:
                instance.status = FeeRecord.Status.OVERDUE
            else:
                payload, status_code = api_response(
                    "Fee status update failed.",
                    errors={"status": ["Status must be one of: paid, unpaid, pending, overdue."]},
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
                return Response(payload, status=status_code)
        else:
            instance.status = FeeRecord.Status.PAID if instance.status in {FeeRecord.Status.UNPAID, FeeRecord.Status.PENDING} else FeeRecord.Status.UNPAID
        instance.save(update_fields=["status", "updated_at"])
        payload, status_code = api_response("Fee status updated successfully.", FeeRecordSerializer(instance).data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)
