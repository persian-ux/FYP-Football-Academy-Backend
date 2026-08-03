from django.contrib import admin

from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "assigned_coach",
        "assigned_sport",
        "academy_group",
        "status",
        "joining_date",
    )
    list_filter = ("status", "gender", "assigned_sport", "academy_group")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "guardian_name",
        "assigned_sport",
        "academy_group",
    )
    readonly_fields = ("created_at", "updated_at")
