from django.db import models


class AttendanceRecord(models.Model):
    status = models.CharField(max_length=20, default="present")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status
