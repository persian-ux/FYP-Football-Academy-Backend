from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rbac.permissions import IsAdmin
from .admin_serializers import (
    AdminUserCreateSerializer,
    AdminUserSerializer,
    AdminUserStatusSerializer,
    AdminUserUpdateSerializer,
)
from .responses import api_response

User = get_user_model()

# Allowed roles for admin management (excludes admin role itself)
MANAGEABLE_ROLES = [User.Role.PLAYER, User.Role.COACH]


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Users"],
        summary="List users (coaches/players)",
        description="List all users with optional role filter. Admin only.",
    ),
)
class AdminUserListAPIView(GenericAPIView):
    """List all users (coaches and players) for admin management."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "phone",
    ]
    ordering_fields = ["id", "email", "first_name", "last_name", "role", "is_active", "date_joined"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = User.objects.filter(role__in=MANAGEABLE_ROLES)

        # Filter by role: ?role=coach or ?role=player
        role = self.request.query_params.get("role")
        if role in MANAGEABLE_ROLES:
            queryset = queryset.filter(role=role)

        # Filter by status: ?is_active=true or ?is_active=false
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ("true", "1", "yes"):
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ("false", "0", "no"):
                queryset = queryset.filter(is_active=False)

        # Search across name/email
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            payload, status_code = api_response(
                "Users retrieved successfully.",
                self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)

        serializer = self.get_serializer(queryset, many=True)
        payload, status_code = api_response(
            "Users retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


@extend_schema_view(
    post=extend_schema(
        tags=["Admin Users"],
        summary="Create a user (coach/player)",
        description="Create a new coach or player account. Admin only.",
    ),
)
class AdminUserCreateAPIView(GenericAPIView):
    """Create a new user (coach or player) as an admin."""

    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            payload, status_code = api_response(
                "User created successfully.",
                AdminUserSerializer(user).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "User creation failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Users"],
        summary="Retrieve a user",
        description="Get details of a specific coach or player. Admin only.",
    ),
    put=extend_schema(
        tags=["Admin Users"],
        summary="Update a user",
        description="Update a coach or player account. Admin only.",
    ),
    patch=extend_schema(
        tags=["Admin Users"],
        summary="Partially update a user",
        description="Partially update a coach or player account. Admin only.",
    ),
    delete=extend_schema(
        tags=["Admin Users"],
        summary="Delete a user",
        description="Delete a coach or player account. Admin only.",
    ),
)
class AdminUserDetailAPIView(APIView):
    """Retrieve, update, or delete a specific user (coach/player)."""

    permission_classes = [IsAdmin]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, role__in=MANAGEABLE_ROLES)

    def get(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        serializer = AdminUserSerializer(user)
        payload, status_code = api_response(
            "User retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def put(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        serializer = AdminUserUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response(
                "User updated successfully.",
                AdminUserSerializer(user).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "User update failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)

    def patch(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response(
                "User updated successfully.",
                AdminUserSerializer(user).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "User update failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)

    def delete(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        user.delete()
        payload, status_code = api_response(
            "User deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        return Response(payload, status=status_code)


@extend_schema_view(
    patch=extend_schema(
        tags=["Admin Users"],
        summary="Toggle user active/inactive status",
        description="Activate or deactivate a coach or player account. Admin only.",
    ),
)
class AdminUserStatusAPIView(APIView):
    """Activate or deactivate a user (coach/player)."""

    permission_classes = [IsAdmin]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, role__in=MANAGEABLE_ROLES)

    def patch(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        serializer = AdminUserStatusSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response(
                "User status updated successfully.",
                AdminUserSerializer(user).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "User status update failed.",
            errors=serializer.errors,
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        return Response(payload, status=status_code)

    def post(self, request, pk, *args, **kwargs):
        """Alias for PATCH — allows toggling via POST for frontend convenience."""
        return self.patch(request, pk, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Users"],
        summary="List coaches",
        description="List all coach accounts. Admin only.",
    ),
)
class AdminCoachListAPIView(GenericAPIView):
    """List all coach users."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "email", "first_name", "last_name", "is_active", "date_joined"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = User.objects.filter(role=User.Role.COACH)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ("true", "1", "yes"):
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ("false", "0", "no"):
                queryset = queryset.filter(is_active=False)

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            payload, status_code = api_response(
                "Coaches retrieved successfully.",
                self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)

        serializer = self.get_serializer(queryset, many=True)
        payload, status_code = api_response(
            "Coaches retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


@extend_schema_view(
    get=extend_schema(
        tags=["Admin Users"],
        summary="List players",
        description="List all player accounts. Admin only.",
    ),
)
class AdminPlayerListAPIView(GenericAPIView):
    """List all player users."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "email", "first_name", "last_name", "is_active", "date_joined"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = User.objects.filter(role=User.Role.PLAYER)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ("true", "1", "yes"):
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ("false", "0", "no"):
                queryset = queryset.filter(is_active=False)

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            payload, status_code = api_response(
                "Players retrieved successfully.",
                self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)

        serializer = self.get_serializer(queryset, many=True)
        payload, status_code = api_response(
            "Players retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)