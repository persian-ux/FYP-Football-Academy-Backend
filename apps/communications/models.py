from django.db import models


class Notification(models.Model):
    channel = models.CharField(max_length=20, default="system")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.channel
