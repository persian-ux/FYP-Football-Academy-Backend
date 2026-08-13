from django.contrib import admin

from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "date", "status", "marked_by", "created_at", "updated_at")
    list_filter = ("status", "date", "user__role")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-date", "-id")