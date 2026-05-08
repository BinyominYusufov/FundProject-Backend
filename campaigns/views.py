from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions

from campaigns.models import Campaign
from campaigns.serializers import CampaignSerializer


class CampaignListView(generics.ListAPIView):
    serializer_class = CampaignSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Campaigns"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Campaign.objects.select_related("organization").order_by("-created_at")


class CampaignDetailView(generics.RetrieveAPIView):
    serializer_class = CampaignSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Campaigns"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Campaign.objects.select_related("organization").order_by("-created_at")
