"""Idempotently create the default dev Organization, admin user, and fund-owner user.

Safe to run on a fresh DB or an already-populated one.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create default dev Organization + admin + fund-owner user (idempotent)."

    def handle(self, *args, **options):
        from config.dev_auth import _bootstrap_dev_entities

        user, org = _bootstrap_dev_entities()
        if user is None or org is None:
            self.stderr.write(self.style.ERROR(
                "Bootstrap failed. Run `python manage.py migrate` first.",
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Organization: pk={org.pk} name='{org.name}' verified={org.verified}",
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Admin user:   pk={user.pk} username='{user.username}' staff={user.is_staff}",
        ))
        self.stdout.write(self.style.SUCCESS("bootstrap_dev complete."))
