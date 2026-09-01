from rest_framework import serializers

from .models import FAQEntry


class FAQSerializer(serializers.ModelSerializer):
    """Used for the public list of available FAQ questions (widget options)."""

    class Meta:
        model = FAQEntry
        fields = ["id", "question", "created_at"]
        read_only_fields = fields


class FAQAnswerSerializer(serializers.ModelSerializer):
    """Used when a visitor selects a question and wants its answer."""

    class Meta:
        model = FAQEntry
        fields = ["id", "question", "answer", "updated_at"]
        read_only_fields = fields