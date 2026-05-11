from __future__ import annotations

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, parsers, permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH
from funds.models import Fund
from funds.serializers import (
    FundCreateSerializer,
    FundPartialUpdateSerializer,
    FundReadSerializer,
)
# from funds.permissions import IsVerifiedFundOwner
# from users.permissions import IsAuthenticatedActiveUser


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

    # AUTH DISABLED FOR DEVELOPMENT MODE
    # Production: permission_classes = (IsAuthenticatedActiveUser, IsVerifiedFundOwner)
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else ()
    parser_classes = (
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    )

    def get_queryset(self) -> QuerySet[Fund]:
        # DEV: все фонды. Продакшен:
        # user = self.request.user
        # if not user.is_authenticated:
        #     return Fund.objects.none()
        # oid = getattr(user, "organization_id", None)
        # if oid is None:
        #     return Fund.objects.none()
        # return (
        #     Fund.objects.filter(organization_id=oid)
        #     .select_related("organization", "created_by")
        #     .order_by("-created_at")
        # )
        return Fund.objects.select_related("organization", "created_by").order_by("-created_at")

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
        return Response(
            {"detail": 'Method "PUT" not allowed. Use PATCH with multipart or JSON.'},
            status=405,
        )
