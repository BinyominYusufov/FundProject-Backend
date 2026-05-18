from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.dev_auth import ENABLE_AUTH, get_dev_user
from myapp.permissions import IsAdminRole
from .models import User
from .permissions import IsAuthenticatedActiveUser
from .serializers import UserSerializer, UserUpdateSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)

    @swagger_auto_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Users"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Users"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self) -> User:
        from config.dev_auth import ensure_dev_entities
        user = get_dev_user(self.request)
        if user is None:
            user, _ = ensure_dev_entities()
        if user is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Bootstrap failed: run `python manage.py migrate` first.")
        return User.objects.select_related("organization").get(pk=user.pk)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class UserListView(generics.ListAPIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser, IsAdminRole)
    serializer_class = UserSerializer

    @swagger_auto_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.select_related("organization").order_by("-created_at")
