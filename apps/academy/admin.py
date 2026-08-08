from django.contrib import admin

from .models import Academy, Section


@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "created_at")
    search_fields = ("name", "location")
    ordering = ("-created_at",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "academy", "coach", "status", "created_at")
    list_filter = ("status", "academy", "coach")
    search_fields = ("name", "description", "coach__email", "coach__first_name", "coach__last_name")
    filter_horizontal = ("players",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
