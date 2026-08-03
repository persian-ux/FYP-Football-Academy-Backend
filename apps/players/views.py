from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from apps.rbac.permissions import IsAdmin, IsAdminOrCoach
from .filters import PlayerQueryFilter
from .models import Player
from .permissions import PlayerAccessPermission
from .serializers import PlayerSerializer


@extend_schema_view(
    list=extend_schema(tags=["Players"], summary="List players"),
    retrieve=extend_schema(tags=["Players"], summary="Retrieve player"),
    create=extend_schema(tags=["Players"], summary="Create player"),
    update=extend_schema(tags=["Players"], summary="Update player"),
    partial_update=extend_schema(tags=["Players"], summary="Update player partially"),
    destroy=extend_schema(tags=["Players"], summary="Delete player"),
)
class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("user", "assigned_coach").all()
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated, PlayerAccessPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "guardian_name",
        "assigned_sport",
        "academy_group",
    ]
    ordering_fields = ["id", "joining_date", "status", "assigned_sport", "academy_group"]
    ordering = ["-id"]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = PlayerQueryFilter.apply(queryset, self.request)

        if user.is_authenticated and getattr(user, "role", None) == "player":
            queryset = queryset.filter(user=user)

        if user.is_authenticated and getattr(user, "role", None) == "coach":
            queryset = queryset.filter(assigned_coach=user)

        return queryset.order_by("-id")

    def get_permissions(self):
        if self.action == "create":
            return [IsAdmin()]
        if self.action == "destroy":
            return [IsAdmin()]
        if self.action in {"list", "retrieve", "update", "partial_update"}:
            return [IsAuthenticated(), PlayerAccessPermission()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Player created successfully.",
                PlayerSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Player creation failed.",
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
            "Players retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Player retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response("Player updated successfully.", serializer.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Player update failed.",
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
        self.check_object_permissions(request, instance)
        instance.delete()
        payload, status_code = api_response("Player deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)
