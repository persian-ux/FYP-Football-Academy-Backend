from typing import Any

from django.db.models import Q


class PlayerQueryFilter:
    """Small, dependency-light filtering utility for Player queries."""

    @staticmethod
    def apply(queryset, request) -> Any:
        params = request.query_params

        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        gender = params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        sport = params.get("assigned_sport")
        if sport:
            queryset = queryset.filter(assigned_sport__icontains=sport)

        group = params.get("academy_group")
        if group:
            queryset = queryset.filter(academy_group__icontains=group)

        coach_id = params.get("assigned_coach")
        if coach_id:
            queryset = queryset.filter(assigned_coach_id=coach_id)

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(guardian_name__icontains=search)
                | Q(assigned_sport__icontains=search)
                | Q(academy_group__icontains=search)
            )

        return queryset
