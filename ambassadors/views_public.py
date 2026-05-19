from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions

from ambassadors.envelope import EnvelopeAPIView, fail, ok
from ambassadors.models import Ambassador, AmbassadorApplication
from ambassadors.serializers import (
    AmbassadorApplicationCreateSerializer,
    AmbassadorApplicationResponseSerializer,
    AmbassadorResponseSerializer,
)


def _parse_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    v = raw.strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    return None


class AmbassadorApplicationCreateView(EnvelopeAPIView):
    """POST /api/ambassador-applications/ — public, no auth."""

    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        tags=["Ambassador Applications"],
        request_body=AmbassadorApplicationCreateSerializer,
    )
    def post(self, request):
        serializer = AmbassadorApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if AmbassadorApplication.objects.filter(
            email__iexact=email,
            status=AmbassadorApplication.Status.PENDING,
        ).exists():
            return fail(
                "An application with this email is already pending review.",
                status=400,
            )
        application = serializer.save(status=AmbassadorApplication.Status.PENDING)
        return ok(
            AmbassadorApplicationResponseSerializer(application).data,
            status=201,
        )


class AmbassadorListView(EnvelopeAPIView):
    """GET /api/ambassadors/ — public; active only; featured first."""

    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Ambassadors"])
    def get(self, request):
        qs = Ambassador.objects.filter(is_active=True).order_by(
            "-is_featured", "-created_at"
        )
        is_featured = _parse_bool(request.query_params.get("is_featured"))
        if is_featured is not None:
            qs = qs.filter(is_featured=is_featured)
        return ok(AmbassadorResponseSerializer(qs, many=True).data)


class AmbassadorDetailView(EnvelopeAPIView):
    """GET /api/ambassadors/<id>/ — public; active only, else 404."""

    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Ambassadors"])
    def get(self, request, pk: int):
        ambassador = Ambassador.objects.filter(pk=pk, is_active=True).first()
        if ambassador is None:
            return fail("Ambassador not found.", status=404)
        return ok(AmbassadorResponseSerializer(ambassador).data)
