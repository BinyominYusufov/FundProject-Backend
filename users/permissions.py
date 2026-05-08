from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from myapp.permissions import (
    FUNOWNERS_GROUP,
    IsAdminRole,
    IsFundOwnerWithOrganization,
    get_active_user,
)
from users.models import User

# Backward-compatible names
IsAdmin = IsAdminRole

__all__ = (
    "FUNOWNERS_GROUP",
    "IsAdmin",
    "IsAdminRole",
    "IsAuthenticatedActiveUser",
    "IsFundOwnerOrAdmin",
    "IsFundOwnerWithOrganization",
    "fund_owner_scoped_organization_id",
    "get_active_user",
    "is_active_admin_request",
)


class IsAuthenticatedActiveUser(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return get_active_user(request) is not None


def is_active_admin_request(request: Request) -> bool:
    u = get_active_user(request)
    return u is not None and u.is_staff


def fund_owner_scoped_organization_id(request: Request) -> int | None:
    u = get_active_user(request)
    if u is None:
        return None
    if not u.groups.filter(name=FUNOWNERS_GROUP).exists():
        return None
    if u.role != User.Role.FUND_OWNER:
        return None
    oid = u.organization_id
    return int(oid) if oid else None


class IsFundOwnerOrAdmin(BasePermission):
    message = "You must be an administrator or a FundOwner with an organization."
    code = "not_fund_owner_or_admin"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if u is None:
            return False
        if u.is_staff:
            return True
        if not u.groups.filter(name=FUNOWNERS_GROUP).exists():
            return False
        if u.role != User.Role.FUND_OWNER:
            return False
        return u.organization_id is not None
