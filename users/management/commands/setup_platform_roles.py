"""Ensure FundOwners group and baseline permissions. Does not create users."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from myapp.permissions import FUNOWNERS_GROUP
from users.models import User


def _perm(app_label: str, model: str, codename: str) -> Permission | None:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        return Permission.objects.get(content_type=ct, codename=codename)
    except (ContentType.DoesNotExist, Permission.DoesNotExist):
        return None


class Command(BaseCommand):
    help = (
        'Create "FundOwners" group if missing and attach read-only model permissions. '
        "Does not create users; use createsuperuser for an admin account."
    )

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=FUNOWNERS_GROUP)
        self.stdout.write(
            self.style.SUCCESS(f'Group "{FUNOWNERS_GROUP}" {"created" if created else "exists"}.'),
        )

        perms: list[Permission] = []
        for app_label, model, code in (
            ("users", "user", "view_user"),
            ("users", "organization", "view_organization"),
            ("users", "campaign", "view_campaign"),
            ("users", "donation", "view_donation"),
        ):
            p = _perm(app_label, model, code)
            if p:
                perms.append(p)

        group.permissions.set(perms)
        self.stdout.write(f"Assigned {len(perms)} permissions to {FUNOWNERS_GROUP}.")

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    "No superuser found. Create one with: python manage.py createsuperuser",
                ),
            )
        else:
            self.stdout.write("Superuser(s) already present.")

        self.stdout.write(self.style.SUCCESS("setup_platform_roles complete."))
