from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
# from rest_framework_simplejwt.authentication import JWTAuthentication

from fund_owner.serializers import OrganizationPublicSerializer, OrganizationWriteSerializer
# from myapp.permissions import IsFundOwnerWithOrganization
from users.models import Organization
# from users.permissions import IsAuthenticatedActiveUser


class OrganizationProfileView(generics.RetrieveUpdateAPIView):
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticatedActiveUser, IsFundOwnerWithOrganization)
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

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
        user = self.request.user
        if user.is_authenticated and getattr(user, "organization_id", None):
            return get_object_or_404(Organization, pk=user.organization_id)
        # DEV: первая организация
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
