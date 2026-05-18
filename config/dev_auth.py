from __future__ import annotations

import logging

from decouple import config

logger = logging.getLogger(__name__)

# DEV-MODE FLAGS
# A fresh clone with no .env file should boot into fully autonomous dev mode.
# Production: set ENABLE_AUTH=true, DEV_PUBLIC_MODE=false, AUTO_BOOTSTRAP=false.
ENABLE_AUTH: bool = config("ENABLE_AUTH", default=False, cast=bool)
DEV_PUBLIC_MODE: bool = config("DEV_PUBLIC_MODE", default=True, cast=bool)
REQUIRE_ADMIN_FOR_DELETE: bool = config("REQUIRE_ADMIN_FOR_DELETE", default=True, cast=bool)

# Bootstrap is enabled whenever auth is disabled OR explicitly opted in.
# This way, even if someone unsets AUTO_BOOTSTRAP, an empty DB still works in dev mode.
_AUTO_BOOTSTRAP_RAW: bool = config("AUTO_BOOTSTRAP", default=True, cast=bool)
AUTO_BOOTSTRAP: bool = _AUTO_BOOTSTRAP_RAW or not ENABLE_AUTH
ALLOW_EMPTY_DATABASE: bool = config("ALLOW_EMPTY_DATABASE", default=True, cast=bool)
MOCK_EXTERNAL_SERVICES: bool = config("MOCK_EXTERNAL_SERVICES", default=True, cast=bool)

DEV_ORG_NAME = "Dev Organization"
DEV_ADMIN_USERNAME = "dev_admin"
DEV_ADMIN_PASSWORD = "dev_password_123!"
DEV_FUND_OWNER_USERNAME = "dev_fund_owner"
DEV_FUND_OWNER_PASSWORD = "dev_password_123!"

# Minimal 1x1 transparent PNG, used to satisfy the organization logo
# requirement when bootstrapping the Dev Organization profile.
_DEV_LOGO_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNg"
    "AAIAAAUAAeImBZsAAAAASUVORK5CYII="
)


def _ensure_dev_org_profile(org) -> None:
    """Fill the Dev Organization's onboarding profile.

    The fund-owner onboarding gate is enforced for everyone, so without this
    the documented fresh-clone flow (`migrate` → `runserver` → create a fund)
    would 403. Idempotent; never raises.
    """
    try:
        import base64

        from django.core.files.base import ContentFile

        from users.models import OrganizationDocument

        changed = []
        if not org.phone_number:
            org.phone_number = "+10000000000"
            changed.append("phone_number")
        if not org.description:
            org.description = "Bootstrapped development organization."
            changed.append("description")
        if not org.country:
            org.country = "Devland"
            changed.append("country")
        if not org.city:
            org.city = "Devcity"
            changed.append("city")
        if not org.address:
            org.address = "1 Dev Street"
            changed.append("address")
        if changed:
            org.save(update_fields=changed)
        if not org.logo:
            org.logo.save(
                "dev_org_logo.png",
                ContentFile(base64.b64decode(_DEV_LOGO_PNG_B64)),
                save=True,
            )
        if not org.documents.exists():
            OrganizationDocument.objects.create(
                organization=org,
                file=ContentFile(
                    b"Bootstrapped development verification document.",
                    name="dev_org_document.txt",
                ),
            )
    except Exception as exc:
        logger.warning("[BOOTSTRAP] Org profile fill skipped: %s", exc)


def _bootstrap_dev_entities():
    """Idempotently materialize the minimum entities the API needs to function.

    Safe to call repeatedly and from any context (views, serializers, signals).
    On any failure (e.g. tables not yet migrated) returns (None, None) instead of raising.
    """
    try:
        from django.contrib.auth.models import Group
        from users.models import Organization, User
    except Exception:
        return None, None

    try:
        org = Organization.objects.order_by("pk").first()
        if org is None:
            org = Organization.objects.create(name=DEV_ORG_NAME, verified=True)
            logger.info("[BOOTSTRAP] Created Organization pk=%s '%s'", org.pk, org.name)
        elif not org.verified:
            org.verified = True
            org.save(update_fields=["verified"])
        _ensure_dev_org_profile(org)

        try:
            from myapp.permissions import FUNOWNERS_GROUP
        except Exception:
            FUNOWNERS_GROUP = "FundOwners"
        fund_owners_group, _ = Group.objects.get_or_create(name=FUNOWNERS_GROUP)

        admin = User.objects.filter(is_staff=True).order_by("pk").first()
        if admin is None:
            admin = User.objects.filter(username=DEV_ADMIN_USERNAME).first()
        if admin is None:
            admin = User.objects.create_user(
                username=DEV_ADMIN_USERNAME,
                password=DEV_ADMIN_PASSWORD,
                name="Dev Admin",
                role=User.Role.ADMIN,
                organization=org,
                is_staff=True,
                is_verified=True,
                is_active=True,
            )
            logger.info("[BOOTSTRAP] Created admin User pk=%s '%s'", admin.pk, admin.username)
        else:
            updated = []
            if admin.organization_id is None:
                admin.organization = org
                updated.append("organization")
            if not admin.is_staff:
                admin.is_staff = True
                updated.append("is_staff")
            if not admin.is_active:
                admin.is_active = True
                updated.append("is_active")
            if not admin.is_verified:
                admin.is_verified = True
                updated.append("is_verified")
            if updated:
                admin.save(update_fields=updated)

        fund_owner = User.objects.filter(role=User.Role.FUND_OWNER).order_by("pk").first()
        if fund_owner is None:
            fund_owner = User.objects.filter(username=DEV_FUND_OWNER_USERNAME).first()
        if fund_owner is None:
            fund_owner = User.objects.create_user(
                username=DEV_FUND_OWNER_USERNAME,
                password=DEV_FUND_OWNER_PASSWORD,
                name="Dev Fund Owner",
                role=User.Role.FUND_OWNER,
                organization=org,
                is_staff=False,
                is_verified=True,
                is_active=True,
            )
            logger.info(
                "[BOOTSTRAP] Created fund-owner User pk=%s '%s'",
                fund_owner.pk,
                fund_owner.username,
            )
        elif fund_owner.organization_id is None:
            fund_owner.organization = org
            fund_owner.save(update_fields=["organization"])
        try:
            fund_owner.groups.add(fund_owners_group)
        except Exception:
            pass

        return admin, org
    except Exception as exc:
        logger.warning("[BOOTSTRAP] Skipped (tables not ready or transient error): %s", exc)
        return None, None


def get_dev_user(request):
    """Return a usable user. Never returns None when dev-mode bootstrap is available."""
    if request is not None and getattr(request, "user", None) is not None:
        u = request.user
        if getattr(u, "is_authenticated", False):
            return u
    if not (DEV_PUBLIC_MODE or not ENABLE_AUTH):
        return None
    try:
        from users.models import User
        user = User.objects.order_by("pk").first()
    except Exception:
        user = None
    if user is None and AUTO_BOOTSTRAP:
        user, _ = _bootstrap_dev_entities()
    return user


def get_dev_organization(request):
    """Return a usable organization. Never returns None when dev-mode bootstrap is available."""
    user = get_dev_user(request)
    if user is not None and getattr(user, "organization_id", None):
        try:
            return user.organization
        except Exception:
            pass
    if not (DEV_PUBLIC_MODE or not ENABLE_AUTH):
        return None
    try:
        from users.models import Organization
        org = Organization.objects.order_by("pk").first()
    except Exception:
        org = None
    if org is None and AUTO_BOOTSTRAP:
        _, org = _bootstrap_dev_entities()
    return org


def ensure_dev_entities():
    """Public alias for bootstrap; callable from views/serializers/management commands."""
    return _bootstrap_dev_entities()


def check_delete_permission(request):
    """Block DELETEs from non-admins when REQUIRE_ADMIN_FOR_DELETE=true."""
    if REQUIRE_ADMIN_FOR_DELETE and request.method == "DELETE":
        from rest_framework.exceptions import PermissionDenied
        user = getattr(request, "user", None)
        if not (user is not None and getattr(user, "is_authenticated", False) and user.is_staff):
            raise PermissionDenied("DELETE operations require administrator access.")
