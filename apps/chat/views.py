from django.shortcuts import render
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from .models import FAQEntry
from .serializers import FAQAnswerSerializer, FAQSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["FAQ Chatbot"],
        summary="List all available FAQ questions (public)",
        description="Public endpoint. Returns only the question list so visitors can pick one.",
    ),
    retrieve=extend_schema(
        tags=["FAQ Chatbot"],
        summary="Retrieve a question and its answer (public)",
    ),
    answer=extend_schema(
        tags=["FAQ Chatbot"],
        summary="Retrieve the answer for a selected question (public)",
    ),
)
class FAQEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only, predefined FAQ chatbot endpoints.

    Accessible to unauthenticated visitors via :class:`AllowAny` without changing
    the project-wide ``IsAuthenticated`` default for other resources.
    """

    queryset = FAQEntry.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    # Keep the widget payload lightweight: no pagination wrapper on a small FAQ list.
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return FAQSerializer
        return FAQAnswerSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        payload, status_code = api_response(
            "FAQ questions retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response(
            "FAQ retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @action(detail=True, methods=["get"], url_path="answer")
    def answer(self, request, pk=None):
        """Return the answer for a single selected question."""
        instance = self.get_object()
        serializer = FAQAnswerSerializer(instance)
        payload, status_code = api_response(
            "FAQ answer retrieved successfully.",
            serializer.data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)


def chatbot_demo(request):
    """Public demo page that embeds the floating FAQ chatbot widget."""
    return render(request, "chatbot_demo.html")