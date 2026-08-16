from django.db import transaction

from .models import Match, MatchEvent, MatchResult


class MatchService:
    """Business logic for match scheduling and results."""

    @staticmethod
    @transaction.atomic
    def create_match(*, home_team, away_team, match_date, venue, notes=None, created_by=None):
        """Create a new scheduled match."""
        return Match.objects.create(
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            venue=venue,
            notes=notes,
            created_by=created_by,
        )

    @staticmethod
    @transaction.atomic
    def update_match(match, **validated_data):
        """Update match details (date, venue, status, notes)."""
        for attr, value in validated_data.items():
            setattr(match, attr, value)
        match.save()
        return match

    @staticmethod
    @transaction.atomic
    def reschedule_match(match, *, new_date, new_venue=None):
        """Reschedule a match to a new date/time (and optionally venue)."""
        if match.status == Match.Status.COMPLETED:
            raise ValueError("A completed match cannot be rescheduled.")
        if match.status == Match.Status.CANCELLED:
            raise ValueError("A cancelled match cannot be rescheduled.")
        match.match_date = new_date
        if new_venue:
            match.venue = new_venue
        match.save()
        return match

    @staticmethod
    @transaction.atomic
    def postpone_match(match, *, new_date=None, notes=None):
        """Postpone a scheduled match."""
        if match.status == Match.Status.COMPLETED:
            raise ValueError("A completed match cannot be postponed.")
        if match.status == Match.Status.CANCELLED:
            raise ValueError("A cancelled match cannot be postponed.")
        match.status = Match.Status.POSTPONED
        if new_date:
            match.match_date = new_date
        if notes:
            match.notes = notes
        match.save()
        return match

    @staticmethod
    @transaction.atomic
    def cancel_match(match, *, notes=None):
        """Cancel a scheduled match."""
        if match.status == Match.Status.COMPLETED:
            raise ValueError("A completed match cannot be cancelled.")
        match.status = Match.Status.CANCELLED
        if notes:
            match.notes = notes
        match.save()
        return match

    @staticmethod
    @transaction.atomic
    def complete_match(match, *, home_score, away_score, duration_minutes=90, events=None, recorded_by=None):
        """Complete a match with final score and optional goal events.

        The winner is automatically calculated from the final score.
        """
        if match.status == Match.Status.COMPLETED:
            raise ValueError("This match is already completed.")
        if match.status == Match.Status.CANCELLED:
            raise ValueError("A cancelled match cannot be completed.")

        result, _ = MatchResult.objects.update_or_create(
            match=match,
            defaults={
                "home_score": home_score,
                "away_score": away_score,
                "duration_minutes": duration_minutes,
                "recorded_by": recorded_by,
            },
        )

        # Replace events if provided
        if events is not None:
            match.events.all().delete()
            for event_data in events:
                MatchEvent.objects.create(match=match, **event_data)

        match.status = Match.Status.COMPLETED
        match.save()
        return match, result