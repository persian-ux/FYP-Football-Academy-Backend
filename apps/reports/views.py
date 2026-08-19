"""Views for student performance reports."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from apps.rbac.permissions import IsAdmin
from .models import StudentReport
from .serializers import StudentReportSerializer


@extend_schema_view(
    list=extend_schema(tags=["Reports"], summary="List student reports"),
    retrieve=extend_schema(tags=["Reports"], summary="Retrieve a student report"),
    create=extend_schema(tags=["Reports"], summary="Create student report (Admin only)"),
    update=extend_schema(tags=["Reports"], summary="Update student report (Admin only)"),
    partial_update=extend_schema(tags=["Reports"], summary="Update student report partially (Admin only)"),
    destroy=extend_schema(tags=["Reports"], summary="Delete student report (Admin only)"),
)
class StudentReportViewSet(viewsets.ModelViewSet):
    queryset = (
        StudentReport.objects.select_related("player", "player__user", "match", "created_by")
        .all()
    )
    serializer_class = StudentReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "player__user__email",
        "player__user__first_name",
        "player__user__last_name",
        "player__academy_group",
        "player__assigned_sport",
        "position",
        "summary",
        "coach_remarks",
    ]
    ordering_fields = [
        "id",
        "report_date",
        "goals",
        "assists",
        "minutes_played",
        "fouls",
        "yellow_cards",
        "red_cards",
        "rating",
        "created_at",
        "updated_at",
    ]
    ordering = ["-report_date", "-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        player = params.get("player")
        if player:
            queryset = queryset.filter(player_id=player)

        match = params.get("match")
        if match:
            queryset = queryset.filter(match_id=match)

        return queryset

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Student report created successfully.",
                StudentReportSerializer(instance, context=self.get_serializer_context()).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Student report creation failed.",
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
            "Student reports retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response(
            "Student report retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response(
                "Student report updated successfully.",
                StudentReportSerializer(instance, context=self.get_serializer_context()).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Student report update failed.",
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
            "Student report deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        return Response(payload, status=status_code)