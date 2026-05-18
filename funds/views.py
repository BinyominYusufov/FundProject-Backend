from __future__ import annotations

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, parsers, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH
from funds.models import Fund
from funds.permissions import FundAccessPermission, OrganizationProfileComplete
from funds.serializers import (
    FundCreateSerializer,
    FundPartialUpdateSerializer,
    FundReadSerializer,
)
from users.models import User
from users.permissions import IsAuthenticatedActiveUser


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        tags=["Funds"],
        consumes=["multipart/form-data"],
        manual_parameters=[
            openapi.Parameter(
                "title",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "description",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "goal_amount",
                openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "category",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="education, health, environment, community, emergency, animals, other",
                required=True,
            ),
            openapi.Parameter(
                "country",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "city",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "address",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "cover_image",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
            ),
            openapi.Parameter(
                "supporting_document",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
            ),
        ],
    ),
)
@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Funds"]))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(tags=["Funds"]))
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        tags=["Funds"],
        consumes=["multipart/form-data", "application/json"],
    ),
)
class FundViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Fund lifecycle for verified fund owners: list / create (multipart) / retrieve / PATCH.
    Organization and creator are derived from the authenticated user.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticatedActiveUser,
        FundAccessPermission,
        OrganizationProfileComplete,
    )
    parser_classes = (
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    )

    def get_queryset(self) -> QuerySet[Fund]:
        qs = Fund.objects.select_related("organization", "created_by").order_by("-created_at")
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return Fund.objects.none()
        if user.is_staff:
            return qs
        if getattr(user, "role", None) == User.Role.FUND_OWNER:
            # Queryset-level ownership scoping: fund_owner sees only own funds.
            return qs.filter(created_by_id=user.pk)
        # Donor (and any other read-only role): see all funds.
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return FundCreateSerializer
        if self.action in ("update", "partial_update"):
            return FundPartialUpdateSerializer
        return FundReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read = FundReadSerializer(instance, context=self.get_serializer_context())
        return Response(read.data, status=201)

    def update(self, request, *args, **kwargs):
        # PUT is intentionally disabled — clients must use PATCH
        return Response(
            {"detail": 'Method "PUT" not allowed. Use PATCH with multipart or JSON.'},
            status=405,
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={**self.get_serializer_context(), "view_action": "partial_update"},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read = FundReadSerializer(instance, context=self.get_serializer_context())
        return Response(read.data)
