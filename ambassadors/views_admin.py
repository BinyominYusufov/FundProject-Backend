from __future__ import annotations

import math

from drf_yasg.utils import swagger_auto_schema
from rest_framework import parsers
from rest_framework_simplejwt.authentication import JWTAuthentication

from ambassadors.envelope import EnvelopeAPIView, fail, ok
from ambassadors.models import Ambassador, AmbassadorApplication
from ambassadors.serializers import (
    AmbassadorApplicationResponseSerializer,
    AmbassadorCreateSerializer,
    AmbassadorResponseSerializer,
    AmbassadorUpdateSerializer,
)
from myapp.permissions import IsAdminRole
from users.permissions import IsAuthenticatedActiveUser


def _parse_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    v = raw.strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None


def _parse_int(raw: str | None, default: int, *, minimum: int = 1) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value >= minimum else default


class AdminView(EnvelopeAPIView):
    """Base: JWT auth + active user + platform admin (is_staff), envelope errors.

    Gated regardless of ENABLE_AUTH (same pattern as FundViewSet / AdminUserViewSet):
    no token -> 401, authenticated non-admin -> 403.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)


# --------------------------------------------------------------------------- #
#  Admin: ambassador applications moderation
# --------------------------------------------------------------------------- #
class AdminAmbassadorApplicationListView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassador Applications"])
    def get(self, request):
        qs = AmbassadorApplication.objects.all().order_by("-created_at")
        status_raw = (request.query_params.get("status") or "").strip().lower()
        if status_raw:
            valid = {c for c, _ in AmbassadorApplication.Status.choices}
            if status_raw not in valid:
                return fail(
                    f"Invalid status. Allowed: {', '.join(sorted(valid))}.",
                    status=422,
                )
            qs = qs.filter(status=status_raw)

        page = _parse_int(request.query_params.get("page"), 1)
        limit = _parse_int(request.query_params.get("limit"), 20)
        total = qs.count()
        pages = math.ceil(total / limit) if total else 0
        start = (page - 1) * limit
        items = qs[start:start + limit]
        return ok(
            {
                "items": AmbassadorApplicationResponseSerializer(items, many=True).data,
                "total": total,
                "page": page,
                "pages": pages,
            }
        )


class AdminAmbassadorApplicationDetailView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassador Applications"])
    def get(self, request, pk: int):
        application = AmbassadorApplication.objects.filter(pk=pk).first()
        if application is None:
            return fail("Ambassador application not found.", status=404)
        return ok(AmbassadorApplicationResponseSerializer(application).data)


class AdminAmbassadorApplicationApproveView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassador Applications"])
    def patch(self, request, pk: int):
        application = AmbassadorApplication.objects.filter(pk=pk).first()
        if application is None:
            return fail("Ambassador application not found.", status=404)
        if application.status != AmbassadorApplication.Status.PENDING:
            return fail("Already reviewed", status=400)
        application.status = AmbassadorApplication.Status.APPROVED
        application.save(update_fields=["status"])
        return ok(AmbassadorApplicationResponseSerializer(application).data)


class AdminAmbassadorApplicationRejectView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassador Applications"])
    def patch(self, request, pk: int):
        application = AmbassadorApplication.objects.filter(pk=pk).first()
        if application is None:
            return fail("Ambassador application not found.", status=404)
        if application.status != AmbassadorApplication.Status.PENDING:
            return fail("Already reviewed", status=400)
        application.status = AmbassadorApplication.Status.REJECTED
        application.save(update_fields=["status"])
        return ok(AmbassadorApplicationResponseSerializer(application).data)


# --------------------------------------------------------------------------- #
#  Admin: ambassador management
# --------------------------------------------------------------------------- #
class AdminAmbassadorListCreateView(AdminView):
    parser_classes = (
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    )

    @swagger_auto_schema(tags=["Admin Ambassadors"])
    def get(self, request):
        qs = Ambassador.objects.all().order_by("-is_featured", "-created_at")
        is_active = _parse_bool(request.query_params.get("is_active"))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        is_featured = _parse_bool(request.query_params.get("is_featured"))
        if is_featured is not None:
            qs = qs.filter(is_featured=is_featured)
        return ok(AmbassadorResponseSerializer(qs, many=True).data)

    @swagger_auto_schema(
        tags=["Admin Ambassadors"],
        request_body=AmbassadorCreateSerializer,
    )
    def post(self, request):
        serializer = AmbassadorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ambassador = serializer.save()
        return ok(AmbassadorResponseSerializer(ambassador).data, status=201)


class AdminAmbassadorDetailView(AdminView):
    parser_classes = (
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    )

    def _get(self, pk: int) -> Ambassador | None:
        return Ambassador.objects.filter(pk=pk).first()

    @swagger_auto_schema(tags=["Admin Ambassadors"])
    def get(self, request, pk: int):
        ambassador = self._get(pk)
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        return ok(AmbassadorResponseSerializer(ambassador).data)

    @swagger_auto_schema(
        tags=["Admin Ambassadors"],
        request_body=AmbassadorUpdateSerializer,
    )
    def patch(self, request, pk: int):
        ambassador = self._get(pk)
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        serializer = AmbassadorUpdateSerializer(
            ambassador, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        old_image = ambassador.image
        replacing_image = "image" in request.FILES
        if replacing_image and old_image:
            old_image.delete(save=False)
        serializer.save()
        return ok(AmbassadorResponseSerializer(ambassador).data)

    @swagger_auto_schema(tags=["Admin Ambassadors"])
    def delete(self, request, pk: int):
        ambassador = self._get(pk)
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        if ambassador.image:
            ambassador.image.delete(save=False)
        ambassador.delete()
        return ok({"deleted": True})


class AdminAmbassadorToggleActiveView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassadors"])
    def patch(self, request, pk: int):
        ambassador = Ambassador.objects.filter(pk=pk).first()
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        ambassador.is_active = not ambassador.is_active
        ambassador.save(update_fields=["is_active"])
        return ok(AmbassadorResponseSerializer(ambassador).data)


class AdminAmbassadorToggleFeaturedView(AdminView):
    @swagger_auto_schema(tags=["Admin Ambassadors"])
    def patch(self, request, pk: int):
        ambassador = Ambassador.objects.filter(pk=pk).first()
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        ambassador.is_featured = not ambassador.is_featured
        ambassador.save(update_fields=["is_featured"])
        return ok(AmbassadorResponseSerializer(ambassador).data)
