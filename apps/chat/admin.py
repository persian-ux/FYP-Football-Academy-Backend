from django.contrib import admin

from .models import ChatMessage, FAQEntry


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "content", "created_at")
    search_fields = ("content",)


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    """Manage FAQ questions/answers from Django Admin without touching code."""

    list_display = ("id", "question", "order", "is_active", "created_at", "updated_at")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    ordering = ("order", "id")
    readonly_fields = ("created_at", "updated_at")