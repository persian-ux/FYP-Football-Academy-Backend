"""Business logic for student performance reports."""

from django.db import transaction

from .models import StudentReport


class StudentReportService:
    """Business logic for student performance reports."""

    @staticmethod
    @transaction.atomic
    def create_report(*, player, match=None, created_by=None, **fields):
        """Create a new student report."""
        return StudentReport.objects.create(
            player=player,
            match=match,
            created_by=created_by,
            **fields,
        )

    @staticmethod
    @transaction.atomic
    def update_report(report, **fields):
        """Update a student report."""
        for attr, value in fields.items():
            setattr(report, attr, value)
        report.save()
        return report