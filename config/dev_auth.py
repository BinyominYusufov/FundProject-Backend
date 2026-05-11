from __future__ import annotations

import logging

from decouple import config

logger = logging.getLogger(__name__)

# AUTH DISABLED FOR DEVELOPMENT MODE
# Control auth behaviour via environment variables.
# Set ENABLE_AUTH=true + DEV_PUBLIC_MODE=false to restore full production auth.
ENABLE_AUTH: bool = config("ENABLE_AUTH", default=True, cast=bool)
DEV_PUBLIC_MODE: bool = config("DEV_PUBLIC_MODE", default=False, cast=bool)
REQUIRE_ADMIN_FOR_DELETE: bool = config("REQUIRE_ADMIN_FOR_DELETE", default=True, cast=bool)

# AUTONOMOUS DEVELOPMENT MODE FLAGS
AUTO_BOOTSTRAP: bool = config("AUTO_BOOTSTRAP", default=False, cast=bool)
ALLOW_EMPTY_DATABASE: bool = config("ALLOW_EMPTY_DATABASE", default=False, cast=bool)
MOCK_EXTERNAL_SERVICES: bool = config("MOCK_EXTERNAL_SERVICES", default=False, cast=bool)


def _bootstrap_dev_entities():
    """AUTO-BOOTSTRAP FALLBACK: Lazily create the minimum required dev Organization and User.

    Safe to call repeatedly — uses get_or_create semantics via order_by+first().
    Never raises; returns (user, org) even if one already existed.
    """
    from users.models import Organization, User

    org = Organization.objects.order_by("pk").first()
    if org is None:
        # DEVELOPMENT MODE BYPASS — auto-create default organization
        org = Organization.objects.create(name="Dev Organization", verified=True)
        logger.info("[AUTO-BOOTSTRAP] Created default Organization pk=%s", org.pk)

    user = User.objects.order_by("pk").first()
    if user is None:
        # DEVELOPMENT MODE BYPASS — auto-create default admin user
        user = User.objects.create_user(
            username="dev_admin",
            password="dev_password_123!",
            name="Dev Admin",
            role=User.Role.ADMIN,
            organization=org,
            is_staff=True,
            is_verified=True,
            is_active=True,
        )
        logger.info(
            "[AUTO-BOOTSTRAP] Created default User pk=%s username=%s",
            user.pk,
            user.username,
        )

    return user, org


def get_dev_user(request):
    """Return authenticated user, or auto-bootstrap a dev user when DEV_PUBLIC_MODE is active."""
    if request.user.is_authenticated:
        return request.user
    if DEV_PUBLIC_MODE:
        from users.models import User
        user = User.objects.order_by("pk").first()
        # AUTO-BOOTSTRAP FALLBACK: create dev user if DB is empty
        if user is None and AUTO_BOOTSTRAP:
            user, _ = _bootstrap_dev_entities()
        return user
    return None


def get_dev_organization(request):
    """Return the user's organization, or auto-bootstrap a dev org in dev public mode."""
    from users.models import Organization
    user = get_dev_user(request)
    if user is not None and getattr(user, "organization_id", None):
        return user.organization
    if DEV_PUBLIC_MODE:
        org = Organization.objects.order_by("pk").first()
        # AUTO-BOOTSTRAP FALLBACK: create dev org if DB is empty
        if org is None and AUTO_BOOTSTRAP:
            _, org = _bootstrap_dev_entities()
        return org
    return None


def check_delete_permission(request):
    """
    Raise PermissionDenied for DELETE requests when REQUIRE_ADMIN_FOR_DELETE=true
    and the requester is not a staff admin. Call this at the top of destroy() handlers.
    """
    if REQUIRE_ADMIN_FOR_DELETE and request.method == "DELETE":
        from rest_framework.exceptions import PermissionDenied
        user = request.user
        if not (user.is_authenticated and user.is_staff):
            raise PermissionDenied("DELETE operations require administrator access.")
