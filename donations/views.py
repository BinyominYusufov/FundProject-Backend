from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH
from campaigns.models import Campaign
from donations.models import Donation
from donations.serializers import DonationCreateSerializer, DonationSerializer
from myapp.permissions import FUNOWNERS_GROUP
from users.models import User
from users.permissions import IsAuthenticatedActiveUser


def donations_queryset_for(user: User) -> QuerySet[Donation]:
    base = Donation.objects.select_related("campaign", "campaign__organization", "user")
    if not ENABLE_AUTH:
        # AUTH DISABLED FOR DEVELOPMENT MODE — return all donations
        return base
    if not isinstance(user, User) or not user.is_active or getattr(user, "is_blocked", False):
        return Donation.objects.none()
    if user.is_staff:
        return base
    if (
        user.groups.filter(name=FUNOWNERS_GROUP).exists()
        and user.role == User.Role.FUND_OWNER
        and user.organization_id
    ):
        return base.filter(campaign__organization_id=user.organization_id)
    return base.filter(user_id=user.pk)


class DonationListView(generics.ListAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)
    serializer_class = DonationSerializer

    @swagger_auto_schema(tags=["Donations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Donation]:
        return donations_queryset_for(self.request.user).order_by("-created_at")


class DonationCreateView(generics.CreateAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)
    serializer_class = DonationCreateSerializer

    @swagger_auto_schema(
        tags=["Donations"],
        responses={201: DonationSerializer},
    )
    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = DonationSerializer(serializer.instance, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(out.data))


class DonationDetailView(generics.RetrieveAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)
    serializer_class = DonationSerializer

    @swagger_auto_schema(tags=["Donations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Donation]:
        return donations_queryset_for(self.request.user)


class CampaignDonationsView(generics.ListAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)
    serializer_class = DonationSerializer

    @swagger_auto_schema(tags=["Donations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Donation]:
        campaign_id = self.kwargs["campaign_id"]
        get_object_or_404(Campaign, pk=campaign_id)
        # DEV: все донаты по кампании
        return (
            Donation.objects.select_related("campaign", "user")
            .filter(campaign_id=campaign_id)
            .order_by("-created_at")
        )
        # Продакшен: фильтрация по роли — см. git history / закомментированный блок выше.
