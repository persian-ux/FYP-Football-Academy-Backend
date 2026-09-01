from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatMessage(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]


class FAQEntry(models.Model):
    """A single predefined question/answer pair shown in the public FAQ chatbot."""

    question = models.CharField(_("Question"), max_length=500)
    answer = models.TextField(_("Answer"))
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("FAQ Entry")
        verbose_name_plural = _("FAQ Entries")

    def __str__(self):
        return self.question
