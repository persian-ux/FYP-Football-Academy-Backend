from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from apps.rbac.permissions import IsAdmin, IsAdminOrCoach
from .models import Academy, Section
from .serializers import AcademySerializer, SectionSerializer


@extend_schema_view(
    list=extend_schema(tags=["Sections"], summary="List sections"),
    retrieve=extend_schema(tags=["Sections"], summary="Retrieve section"),
    create=extend_schema(tags=["Sections"], summary="Create section"),
    update=extend_schema(tags=["Sections"], summary="Update section"),
    partial_update=extend_schema(tags=["Sections"], summary="Update section partially"),
    destroy=extend_schema(tags=["Sections"], summary="Delete section"),
)
class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.select_related("coach", "academy").prefetch_related("players").all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrCoach]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "coach__email", "coach__first_name", "coach__last_name"]
    ordering_fields = ["id", "name", "status", "created_at"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated and getattr(user, "role", None) == "coach":
            queryset = queryset.filter(coach=user)

        return queryset.order_by("-id")

    def get_permissions(self):
        if self.action in {"create", "destroy"}:
            return [IsAdmin()]
        if self.action in {"update", "partial_update"}:
            return [IsAdmin()]
        return [IsAuthenticated(), IsAdminOrCoach()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Section created successfully.",
                SectionSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Section creation failed.",
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
            "Sections retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Section retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response("Section updated successfully.", serializer.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Section update failed.",
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
        payload, status_code = api_response("Section deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)


@extend_schema_view(
    list=extend_schema(tags=["Academies"], summary="List academies"),
    retrieve=extend_schema(tags=["Academies"], summary="Retrieve academy"),
    create=extend_schema(tags=["Academies"], summary="Create academy"),
    update=extend_schema(tags=["Academies"], summary="Update academy"),
    partial_update=extend_schema(tags=["Academies"], summary="Update academy partially"),
    destroy=extend_schema(tags=["Academies"], summary="Delete academy"),
)
class AcademyViewSet(viewsets.ModelViewSet):
    queryset = Academy.objects.all()
    serializer_class = AcademySerializer
    permission_classes = [IsAuthenticated, IsAdminOrCoach]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "location"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["-id"]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsAuthenticated(), IsAdminOrCoach()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Academy created successfully.",
                AcademySerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Academy creation failed.",
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
            "Academies retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Academy retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            payload, status_code = api_response("Academy updated successfully.", serializer.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Academy update failed.",
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
        payload, status_code = api_response("Academy deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)