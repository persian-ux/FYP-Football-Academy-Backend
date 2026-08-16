from django.contrib import admin

from .models import Match, MatchEvent, MatchResult, Team


class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 0
    fields = ("event_type", "team", "scorer", "scorer_name", "minute", "assist", "assist_name")
    autocomplete_fields = ("team",)


class MatchResultInline(admin.StackedInline):
    model = MatchResult
    extra = 0
    fields = ("home_score", "away_score", "duration_minutes", "winner", "recorded_by")
    readonly_fields = ("winner",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "short_code", "coach", "created_at")
    list_filter = ("coach",)
    search_fields = ("name", "short_code", "description", "coach__email", "coach__first_name", "coach__last_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "home_team", "away_team", "match_date", "venue", "status", "created_at")
    list_filter = ("status", "match_date", "venue")
    search_fields = ("venue", "notes", "home_team__name", "away_team__name")
    autocomplete_fields = ("home_team", "away_team")
    readonly_fields = ("created_at", "updated_at")
    inlines = (MatchResultInline, MatchEventInline)
    ordering = ("match_date",)
    date_hierarchy = "match_date"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ("id", "match", "home_score", "away_score", "winner", "duration_minutes", "recorded_by", "created_at")
    list_filter = ("winner",)
    search_fields = ("match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match",)
    readonly_fields = ("winner", "created_at", "updated_at")


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("id", "match", "event_type", "team", "scorer", "scorer_name", "minute", "assist", "assist_name")
    list_filter = ("event_type", "team")
    search_fields = ("scorer_name", "assist_name", "match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match", "team")
    readonly_fields = ("created_at",)
