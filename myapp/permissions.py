from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from users.models import User

FUNOWNERS_GROUP = "FundOwners"


def get_active_user(request: Request) -> User | None:
    u = request.user
    if not u.is_authenticated or isinstance(u, AnonymousUser):
        return None
    if not isinstance(u, User):
        return None
    if not u.is_active or getattr(u, "is_blocked", False):
        return None
    return u


class IsAdminRole(BasePermission):
    """Platform administrator: Django `is_staff` (not hardcoded user ids)."""

    message = "Only platform administrators can perform this action."
    code = "not_admin"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        return bool(u and u.is_staff)

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsFundOwner(BasePermission):
    """User belongs to the `FundOwners` auth group."""

    message = "Only FundOwners can access this resource."
    code = "not_fund_owner"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if not u:
            return False
        return u.groups.filter(name=FUNOWNERS_GROUP).exists()

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsFundOwnerWithOrganization(BasePermission):
    """FundOwners group + fund_owner role + linked organization (manage own campaigns)."""

    message = "Only FundOwners with an assigned organization can perform this action."
    code = "not_fund_owner_org"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if not u:
            return False
        if not u.groups.filter(name=FUNOWNERS_GROUP).exists():
            return False
        if u.role != User.Role.FUND_OWNER:
            return False
        return u.organization_id is not None

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsOwnerOfObject(BasePermission):
    """Object-level: default owner field `user` matches request user. Staff may access any."""

    message = "You can only access your own data."
    code = "not_owner"
    owner_attr = "user"

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_active_user(request) is not None

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        u = get_active_user(request)
        if not u:
            return False
        if u.is_staff:
            return True
        owner = getattr(obj, self.owner_attr, None)
        if owner is None:
            return False
        oid = getattr(owner, "pk", owner)
        return oid == u.pk


class IsAdminOrFundOwner(BasePermission):
    """Staff admin, or managing FundOwner (group + role + organization)."""

    message = "Only administrators or FundOwners with an organization can perform this action."
    code = "not_admin_or_fund_owner"

    def has_permission(self, request: Request, view: Any) -> bool:
        u = get_active_user(request)
        if not u:
            return False
        if u.is_staff:
            return True
        if not u.groups.filter(name=FUNOWNERS_GROUP).exists():
            return False
        if u.role != User.Role.FUND_OWNER:
            return False
        return u.organization_id is not None

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)


class ReadOnly(BasePermission):
    """Allow only safe HTTP methods (GET, HEAD, OPTIONS)."""

    message = "Write operations are not allowed for this role."
    code = "read_only"

    def has_permission(self, request: Request, view: Any) -> bool:
        return request.method in SAFE_METHODS

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return request.method in SAFE_METHODS
