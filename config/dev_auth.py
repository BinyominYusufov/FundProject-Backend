from __future__ import annotations

from decouple import config

# AUTH DISABLED FOR DEVELOPMENT MODE
# Control auth behaviour via environment variables.
# Set ENABLE_AUTH=true + DEV_PUBLIC_MODE=false to restore full production auth.
ENABLE_AUTH: bool = config("ENABLE_AUTH", default=True, cast=bool)
DEV_PUBLIC_MODE: bool = config("DEV_PUBLIC_MODE", default=False, cast=bool)
REQUIRE_ADMIN_FOR_DELETE: bool = config("REQUIRE_ADMIN_FOR_DELETE", default=True, cast=bool)


def get_dev_user(request):
    """Return authenticated user, or the first DB user when DEV_PUBLIC_MODE is active."""
    if request.user.is_authenticated:
        return request.user
    if DEV_PUBLIC_MODE:
        from users.models import User
        return User.objects.order_by("pk").first()
    return None


def get_dev_organization(request):
    """Return the user's organization, or the first DB organization in dev public mode."""
    from users.models import Organization
    user = get_dev_user(request)
    if user is not None and getattr(user, "organization_id", None):
        return user.organization
    if DEV_PUBLIC_MODE:
        return Organization.objects.order_by("pk").first()
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
