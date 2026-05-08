from __future__ import annotations

from django.db.models import Q, QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from donations.models import Donation
from donations.serializers import AdminDonationSerializer, DonationSerializer
from myapp.permissions import IsAdminRole, IsFundOwnerWithOrganization
from users.permissions import (
    IsAuthenticatedActiveUser,
    fund_owner_scoped_organization_id,
    is_active_admin_request,
)


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Admin"]))
class AdminDonationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)
    serializer_class = AdminDonationSerializer

    def get_queryset(self) -> QuerySet[Donation]:
        if not is_active_admin_request(self.request):
            return Donation.objects.none()
        qs = Donation.objects.select_related("campaign", "campaign__organization", "user").order_by(
            "-created_at"
        )
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            q = Q(campaign__name__icontains=search) | Q(campaign__organization__name__icontains=search) | Q(
                user__username__icontains=search
            ) | Q(user__email__icontains=search)
            if search.isdigit():
                try:
                    n = int(search)
                    q |= Q(id=n) | Q(amount=n)
                except (OverflowError, ValueError):
                    pass
            qs = qs.filter(q)
        return qs


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Fund owner"]))
class FundOwnerDonationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsFundOwnerWithOrganization)
    serializer_class = DonationSerializer

    def get_queryset(self) -> QuerySet[Donation]:
        oid = fund_owner_scoped_organization_id(self.request)
        if oid is None:
            return Donation.objects.none()
        return (
            Donation.objects.select_related("campaign", "campaign__organization", "user")
            .filter(campaign__organization_id=oid)
            .order_by("-created_at")
        )
