from __future__ import annotations

from typing import Any, Final

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from myapp.permissions import IsAdminRole
from users.models import User
from users.pagination import AdminUserPagination
from users.permissions import IsAuthenticatedActiveUser
from users.querysets import with_admin_list_annotations
from users.serializers import (
    AdminUserListSerializer,
    AdminUserSerializer,
)


_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    ("all", "verified", "unverified", "blocked")
)


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="verify", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="block", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="unblock", decorator=swagger_auto_schema(tags=["Admin"]))
class AdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)
    serializer_class = AdminUserSerializer
    pagination_class = AdminUserPagination

    def get_serializer_class(
        self,
    ) -> (
        type[AdminUserListSerializer]
        | type[AdminUserSerializer]
    ):
        if self.action in ("list", "verify", "block", "unblock"):
            return AdminUserListSerializer
        return AdminUserSerializer

    def get_queryset(self) -> QuerySet[User]:
        # DEV: без проверки админа
        # if not is_active_admin_request(self.request):
        #     return User.objects.none()
        qs: QuerySet[User] = User.objects.select_related("organization").order_by("-created_at")
        if self.action != "list":
            return qs
        status_raw = (self.request.query_params.get("status") or "all").strip().lower()
        if status_raw not in _STATUS_VALUES:
            raise ValidationError(
                {
                    "status": (
                        f"Invalid value. Allowed: {', '.join(sorted(_STATUS_VALUES))}."
                    )
                }
            )
        if status_raw == "verified":
            qs = qs.filter(is_verified=True, is_blocked=False)
        elif status_raw == "unverified":
            qs = qs.filter(is_verified=False, is_blocked=False)
        elif status_raw == "blocked":
            qs = qs.filter(is_blocked=True)
        return with_admin_list_annotations(qs)

    def _list_payload_for_user_id(self, user_id: int) -> dict[str, Any]:
        user = with_admin_list_annotations(
            User.objects.select_related("organization").filter(pk=user_id)
        ).get()
        return AdminUserListSerializer(user, context=self.get_serializer_context()).data

    @action(detail=True, methods=["patch"], url_path="verify")
    def verify(self, request: Request, pk: Any = None) -> Response:
        user = self.get_object()
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return Response(self._list_payload_for_user_id(user.pk))

    @action(detail=True, methods=["patch"], url_path="block")
    def block(self, request: Request, pk: Any = None) -> Response:
        user = self.get_object()
        if user.pk == getattr(request.user, "pk", None):
            return Response(
                {"detail": "Cannot block yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_blocked = True
        user.save(update_fields=["is_blocked"])
        return Response(self._list_payload_for_user_id(user.pk))

    @action(detail=True, methods=["patch"], url_path="unblock")
    def unblock(self, request: Request, pk: Any = None) -> Response:
        user = self.get_object()
        user.is_blocked = False
        user.save(update_fields=["is_blocked"])
        return Response(self._list_payload_for_user_id(user.pk))
