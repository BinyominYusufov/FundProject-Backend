from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, parsers, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH
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
    # Profile editing accepts file uploads (logo + verification documents).
    parser_classes = (
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
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
        from config.dev_auth import ensure_dev_entities, get_dev_organization
        org = get_dev_organization(self.request)
        if org is None:
            _, org = ensure_dev_entities()
        if org is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Bootstrap failed: run `python manage.py migrate` first.")
        return org

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
