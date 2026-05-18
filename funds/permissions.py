from __future__ import annotations

from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from myapp.permissions import get_active_user
from users.models import Organization, User


class FundAccessPermission(BasePermission):
    """
    Role-aware permission for /api/funds/:
      - Anonymous → 401 (require auth)
      - SAFE methods → any authenticated user
      - POST → fund_owner role only
      - PATCH/DELETE → fund_owner (own) or admin
      - Donors → never write
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if u is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        if u.is_staff:
            return True
        if u.role != User.Role.FUND_OWNER:
            return False
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        u = get_active_user(request)
        if u is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        if u.is_staff:
            return True
        if u.role != User.Role.FUND_OWNER:
            return False
        return int(getattr(obj, "created_by_id", 0)) == int(u.pk)


class OrganizationProfileComplete(BasePermission):
    """Onboarding gate: a fund owner must finish the organization profile.

    Blocks fund creation and fund management (any write) until the linked
    organization has every required onboarding field filled in. Read access
    (SAFE methods) is always allowed. Staff and non-fund-owner roles are not
    governed here — auth/role rejection is left to the other permission
    classes on the view.
    """

    message = "Complete your organization profile before creating a fund."
    code = "organization_profile_incomplete"

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        u = get_active_user(request)
        if u is None or u.is_staff or u.role != User.Role.FUND_OWNER:
            # Let IsAuthenticatedActiveUser / FundAccessPermission decide.
            return True
        oid = u.organization_id
        org = None
        if oid is not None:
            try:
                org = Organization.objects.get(pk=oid)
            except Organization.DoesNotExist:
                org = None
        if org is None:
            self.message = (
                "Your account must be linked to an organization "
                "before creating a fund."
            )
            self.code = "no_organization"
            return False
        if not org.is_profile_complete:
            missing = ", ".join(org.missing_profile_fields)
            self.message = (
                "Complete your organization profile before creating a fund. "
                f"Missing: {missing}."
            )
            self.code = "organization_profile_incomplete"
            return False
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsVerifiedFundOwner(BasePermission):
    """
    Active user with role fund_owner, linked organization, and verified organization.
    Unverified organization → 403.
    """

    message = "Only fund owners with a verified organization can manage funds."
    code = "not_verified_fund_owner"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if u is None:
            return False
        if u.role != User.Role.FUND_OWNER:
            self.message = "Only fund owners can perform this action."
            self.code = "not_fund_owner"
            return False
        oid = u.organization_id
        if oid is None:
            self.message = "Your account must be linked to an organization."
            self.code = "no_organization"
            return False
        try:
            org = Organization.objects.only("verified").get(pk=oid)
        except Organization.DoesNotExist:
            from config.dev_auth import AUTO_BOOTSTRAP, ensure_dev_entities
            if AUTO_BOOTSTRAP:
                _, org = ensure_dev_entities()
                if org is None:
                    self.message = "Organization not found."
                    self.code = "organization_missing"
                    return False
            else:
                self.message = "Organization not found."
                self.code = "organization_missing"
                return False
        if not org.verified:
            self.message = "Organization must be verified to create or manage funds."
            self.code = "organization_not_verified"
            return False
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if not self.has_permission(request, view):
            return False
        u = get_active_user(request)
        assert u is not None
        return int(obj.organization_id) == int(u.organization_id)
