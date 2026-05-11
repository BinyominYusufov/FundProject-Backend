from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH, get_dev_user
from fund_owner.serializers import OrganizationPublicSerializer, OrganizationWriteSerializer
from myapp.permissions import IsFundOwnerWithOrganization
from users.models import Organization
from users.permissions import IsAuthenticatedActiveUser


class OrganizationProfileView(generics.RetrieveUpdateAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    # Production: authentication_classes = (JWTAuthentication,)
    # Production: permission_classes = (IsAuthenticatedActiveUser, IsFundOwnerWithOrganization)
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (
        (permissions.AllowAny,) if not ENABLE_AUTH
        else (IsAuthenticatedActiveUser, IsFundOwnerWithOrganization)
    )

    @swagger_auto_schema(tags=["Fund owner"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Fund owner"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Fund owner"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self) -> Organization:
        # AUTH DISABLED FOR DEVELOPMENT MODE
        user = get_dev_user(self.request)
        if user is not None and getattr(user, "organization_id", None):
            return get_object_or_404(Organization, pk=user.organization_id)
        first = Organization.objects.order_by("pk").first()
        return get_object_or_404(Organization, pk=first.pk) if first else get_object_or_404(Organization, pk=0)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return OrganizationWriteSerializer
        return OrganizationPublicSerializer


class OrganizationListView(generics.ListAPIView):
    serializer_class = OrganizationPublicSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Organizations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Organization.objects.filter(verified=True).order_by("-created_at")


class OrganizationDetailView(generics.RetrieveAPIView):
    serializer_class = OrganizationPublicSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Organizations"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Organization.objects.filter(verified=True)
