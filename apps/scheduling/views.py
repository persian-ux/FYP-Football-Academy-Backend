from django.utils import timezone
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.v1.responses import api_response
from apps.rbac.permissions import IsAdmin, IsAdminOrCoach, is_admin, is_coach
from .models import Match, Team
from .serializers import (
    MatchCompleteSerializer,
    MatchSerializer,
    TeamSerializer,
)
from .services import MatchService


@extend_schema_view(
    list=extend_schema(tags=["Teams"], summary="List teams"),
    retrieve=extend_schema(tags=["Teams"], summary="Retrieve team"),
    create=extend_schema(tags=["Teams"], summary="Create team"),
    update=extend_schema(tags=["Teams"], summary="Update team"),
    partial_update=extend_schema(tags=["Teams"], summary="Update team partially"),
    destroy=extend_schema(tags=["Teams"], summary="Delete team"),
)
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("coach").all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "short_code", "description", "coach__email", "coach__first_name", "coach__last_name"]
    ordering_fields = ["id", "name", "short_code", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAdmin()]
        if self.action in {"update", "partial_update", "destroy"}:
            return [IsAdminOrCoach()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_coach(self.request.user):
            queryset = queryset.filter(coach=self.request.user)
        return queryset

    def perform_create(self, serializer):
        if is_coach(self.request.user):
            raise serializers.ValidationError("Coaches can only manage existing teams assigned to them.")
        serializer.save()

    def perform_update(self, serializer):
        if is_coach(self.request.user) and serializer.validated_data.get("coach", self.get_object().coach) != self.request.user:
            raise serializers.ValidationError("A coach cannot assign a team to another coach.")
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            payload, status_code = api_response(
                "Team created successfully.",
                TeamSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Team creation failed.",
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
            "Teams retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Team retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            if is_coach(request.user) and serializer.validated_data.get("coach", instance.coach) != request.user:
                payload, status_code = api_response(
                    "Team update failed.",
                    errors={"coach": ["A coach cannot assign a team to another coach."]},
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
                return Response(payload, status=status_code)
            serializer.save()
            payload, status_code = api_response("Team updated successfully.", serializer.data, status_code=status.HTTP_200_OK)
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Team update failed.",
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
        payload, status_code = api_response("Team deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)


@extend_schema_view(
    list=extend_schema(tags=["Matches"], summary="List matches (filter by team/status/date)"),
    retrieve=extend_schema(tags=["Matches"], summary="Retrieve match details"),
    create=extend_schema(tags=["Matches"], summary="Create match (Admin only)"),
    update=extend_schema(tags=["Matches"], summary="Update match (Admin only)"),
    partial_update=extend_schema(tags=["Matches"], summary="Update match partially (Admin only)"),
    destroy=extend_schema(tags=["Matches"], summary="Delete match (Admin only)"),
)
class MatchViewSet(viewsets.ModelViewSet):
    queryset = (
        Match.objects.select_related("home_team", "away_team", "created_by")
        .prefetch_related("result", "events", "events__team", "events__scorer", "events__assist")
        .all()
    )
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["venue", "notes", "home_team__name", "away_team__name"]
    ordering_fields = ["id", "match_date", "status", "venue", "created_at"]
    ordering = ["match_date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        if is_coach(self.request.user):
            queryset = queryset.filter(
                models.Q(home_team__coach=self.request.user)
                | models.Q(away_team__coach=self.request.user)
            )

        team = params.get("team")
        if team:
            queryset = queryset.filter(home_team_id=team) | queryset.filter(away_team_id=team)

        status_param = params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        date = params.get("date")
        if date:
            queryset = queryset.filter(match_date__date=date)

        return queryset

    def get_permissions(self):
        if self.action in {
            "create",
            "update",
            "partial_update",
            "destroy",
            "reschedule",
            "postpone",
            "cancel",
            "complete",
        }:
            return [IsAdminOrCoach()]
        return [IsAuthenticated()]

    def _coach_can_manage_teams(self, home_team, away_team):
        return is_admin(self.request.user) or (
            home_team.coach_id == self.request.user.id or away_team.coach_id == self.request.user.id
        )

    def _validate_coach_teams(self, home_team, away_team):
        if is_coach(self.request.user) and not self._coach_can_manage_teams(home_team, away_team):
            raise serializers.ValidationError("A coach can only schedule matches involving their teams.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                self._validate_coach_teams(
                    serializer.validated_data["home_team"], serializer.validated_data["away_team"]
                )
            except serializers.ValidationError as exc:
                serializer._errors = {"detail": exc.detail}
            if serializer.errors:
                payload, status_code = api_response("Match creation failed.", errors=serializer.errors, success=False, status_code=status.HTTP_400_BAD_REQUEST)
                return Response(payload, status=status_code)
            instance = MatchService.create_match(
                home_team=serializer.validated_data["home_team"],
                away_team=serializer.validated_data["away_team"],
                match_date=serializer.validated_data["match_date"],
                venue=serializer.validated_data["venue"],
                notes=serializer.validated_data.get("notes"),
                created_by=request.user,
            )
            payload, status_code = api_response(
                "Match created successfully.",
                MatchSerializer(instance).data,
                status_code=status.HTTP_201_CREATED,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Match creation failed.",
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
            "Matches retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload, status_code = api_response("Match retrieved successfully.", serializer.data, status_code=status.HTTP_200_OK)
        return Response(payload, status=status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                self._validate_coach_teams(
                    serializer.validated_data.get("home_team", instance.home_team),
                    serializer.validated_data.get("away_team", instance.away_team),
                )
            except serializers.ValidationError as exc:
                payload, status_code = api_response("Match update failed.", errors={"detail": exc.detail}, success=False, status_code=status.HTTP_400_BAD_REQUEST)
                return Response(payload, status=status_code)
            instance = MatchService.update_match(instance, **serializer.validated_data)
            payload, status_code = api_response(
                "Match updated successfully.",
                MatchSerializer(instance).data,
                status_code=status.HTTP_200_OK,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Match update failed.",
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
        payload, status_code = api_response("Match deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="List upcoming matches",
        description="Return matches scheduled in the future, ordered chronologically.",
    )
    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        queryset = self.get_queryset().filter(
            match_date__gte=timezone.now(),
            status__in=[Match.Status.SCHEDULED, Match.Status.POSTPONED],
        ).order_by("match_date")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        payload, status_code = api_response(
            "Upcoming matches retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="List today's matches",
        description="Return matches scheduled for today, ordered chronologically.",
    )
    @action(detail=False, methods=["get"])
    def today(self, request):
        today = timezone.localdate()
        queryset = self.get_queryset().filter(match_date__date=today).order_by("match_date")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        payload, status_code = api_response(
            "Today's matches retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="List completed results",
        description="Return completed matches with final scores and auto-calculated winners.",
    )
    @action(detail=False, methods=["get"])
    def results(self, request):
        queryset = self.get_queryset().filter(status=Match.Status.COMPLETED).order_by("-match_date")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        payload, status_code = api_response(
            "Completed results retrieved successfully.",
            self.get_paginated_response(serializer.data).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="Reschedule a match (Admin only)",
        description="Change the date/time (and optionally venue) of a scheduled match.",
        request=inline_serializer(
            "RescheduleRequest",
            {
                "new_date": serializers.DateTimeField(),
                "new_venue": serializers.CharField(required=False, allow_blank=True),
            },
        ),
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def reschedule(self, request, pk=None):
        match = self.get_object()
        new_date = request.data.get("new_date")
        new_venue = request.data.get("new_venue")
        if not new_date:
            payload, status_code = api_response(
                "Reschedule failed.",
                errors={"new_date": ["This field is required."]},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)
        try:
            match = MatchService.reschedule_match(match, new_date=new_date, new_venue=new_venue)
        except ValueError as exc:
            payload, status_code = api_response(
                "Reschedule failed.",
                errors={"detail": str(exc)},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Match rescheduled successfully.",
            MatchSerializer(match).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="Postpone a match (Admin only)",
        description="Mark a scheduled match as postponed, optionally with a new date.",
        request=inline_serializer(
            "PostponeRequest",
            {
                "new_date": serializers.DateTimeField(required=False),
                "notes": serializers.CharField(required=False, allow_blank=True),
            },
        ),
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def postpone(self, request, pk=None):
        match = self.get_object()
        new_date = request.data.get("new_date")
        notes = request.data.get("notes")
        try:
            match = MatchService.postpone_match(match, new_date=new_date, notes=notes)
        except ValueError as exc:
            payload, status_code = api_response(
                "Postpone failed.",
                errors={"detail": str(exc)},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Match postponed successfully.",
            MatchSerializer(match).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="Cancel a match (Admin only)",
        description="Mark a scheduled match as cancelled.",
        request=inline_serializer(
            "CancelRequest",
            {
                "notes": serializers.CharField(required=False, allow_blank=True),
            },
        ),
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def cancel(self, request, pk=None):
        match = self.get_object()
        notes = request.data.get("notes")
        try:
            match = MatchService.cancel_match(match, notes=notes)
        except ValueError as exc:
            payload, status_code = api_response(
                "Cancel failed.",
                errors={"detail": str(exc)},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)
        payload, status_code = api_response(
            "Match cancelled successfully.",
            MatchSerializer(match).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)

    @extend_schema(
        tags=["Matches"],
        summary="Complete a match and enter final result (Admin only)",
        description=(
            "Enter the final home/away scores, duration and optional goal events. "
            "The winner is automatically calculated from the final score."
        ),
        request=MatchCompleteSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrCoach])
    def complete(self, request, pk=None):
        match = self.get_object()
        serializer = MatchCompleteSerializer(data=request.data, context={"match": match})
        if not serializer.is_valid():
            payload, status_code = api_response(
                "Match completion failed.",
                errors=serializer.errors,
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        events_data = serializer.validated_data.get("events", [])
        events = []
        for event_data in events_data:
            events.append(
                {
                    "event_type": event_data.get("event_type", "goal"),
                    "team": event_data["team"],
                    "scorer": event_data.get("scorer"),
                    "scorer_name": event_data.get("scorer_name"),
                    "minute": event_data["minute"],
                    "assist": event_data.get("assist"),
                    "assist_name": event_data.get("assist_name"),
                }
            )

        try:
            match, result = MatchService.complete_match(
                match,
                home_score=serializer.validated_data["home_score"],
                away_score=serializer.validated_data["away_score"],
                duration_minutes=serializer.validated_data.get("duration_minutes", 90),
                events=events,
                recorded_by=request.user,
            )
        except ValueError as exc:
            payload, status_code = api_response(
                "Match completion failed.",
                errors={"detail": str(exc)},
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return Response(payload, status=status_code)

        payload, status_code = api_response(
            "Match completed successfully.",
            MatchSerializer(match).data,
            status_code=status.HTTP_200_OK,
        )
        return Response(payload, status=status_code)
