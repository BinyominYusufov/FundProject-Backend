from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from myapp.permissions import get_active_user
from users.models import Organization, User


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
