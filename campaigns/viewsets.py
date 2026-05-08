from __future__ import annotations

from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from myapp.permissions import IsAdminRole, IsFundOwnerWithOrganization
from users.permissions import (
    IsAuthenticatedActiveUser,
    fund_owner_scoped_organization_id,
    is_active_admin_request,
)

from .models import Campaign
from .serializers import (
    AdminCampaignSerializer,
    FundOwnerCampaignCreateSerializer,
    FundOwnerCampaignSerializer,
)


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="destroy", decorator=swagger_auto_schema(tags=["Admin"]))
class AdminCampaignViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)
    serializer_class = AdminCampaignSerializer

    def get_queryset(self) -> QuerySet[Campaign]:
        if not is_active_admin_request(self.request):
            return Campaign.objects.none()
        return Campaign.objects.select_related("organization").order_by("-created_at")


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Campaigns"]))
@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        tags=["Campaigns"],
        request_body=FundOwnerCampaignCreateSerializer,
        responses={201: FundOwnerCampaignSerializer},
    ),
)
class FundOwnerCampaignViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsFundOwnerWithOrganization)
    serializer_class = FundOwnerCampaignSerializer

    def get_queryset(self) -> QuerySet[Campaign]:
        oid = fund_owner_scoped_organization_id(self.request)
        if oid is None:
            return Campaign.objects.none()
        return (
            Campaign.objects.select_related("organization")
            .filter(organization_id=oid)
            .order_by("-created_at")
        )

    def get_serializer_class(self) -> type[FundOwnerCampaignCreateSerializer] | type[FundOwnerCampaignSerializer]:
        if self.request.method == "POST":
            return FundOwnerCampaignCreateSerializer
        return FundOwnerCampaignSerializer
