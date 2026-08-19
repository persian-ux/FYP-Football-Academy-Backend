from django.contrib import admin

from .models import StudentReport


@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "player",
        "match",
        "report_date",
        "position",
        "goals",
        "assists",
        "minutes_played",
        "fouls",
        "yellow_cards",
        "red_cards",
        "rating",
        "created_by",
        "created_at",
    ]
    list_filter = ["report_date", "position", "created_at"]
    search_fields = [
        "player__user__first_name",
        "player__user__last_name",
        "player__user__email",
        "player__academy_group",
        "summary",
        "coach_remarks",
        "position",
    ]
    autocomplete_fields = ["player"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-report_date", "-created_at"]