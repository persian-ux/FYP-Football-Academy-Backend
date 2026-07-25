from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Seed / ensure the default admin user always exists and is active."

    def handle(self, *args, **options):
        email = "admin@sportsphere.com"
        password = "admin@123"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "password": password,
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Admin user '{email}' created successfully."))
        else:
            # Always ensure the admin is active and has correct permissions
            needs_update = False
            if not user.is_active:
                user.is_active = True
                needs_update = True
            if not user.is_staff:
                user.is_staff = True
                needs_update = True
            if not user.is_superuser:
                user.is_superuser = True
                needs_update = True
            if user.role != User.Role.ADMIN:
                user.role = User.Role.ADMIN
                needs_update = True

            if needs_update:
                user.save(update_fields=["is_active", "is_staff", "is_superuser", "role"])
                self.stdout.write(self.style.SUCCESS(f"Admin user '{email}' has been reactivated / updated."))
            else:
                self.stdout.write(self.style.WARNING(f"Admin user '{email}' already exists and is active."))