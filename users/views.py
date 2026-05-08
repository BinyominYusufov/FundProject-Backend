from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from myapp.permissions import IsAdminRole
from rest_framework import generics
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User
from .permissions import IsAuthenticatedActiveUser
from .serializers import UserSerializer, UserUpdateSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser,)

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
        u: User = self.request.user
        return User.objects.select_related("organization").get(pk=u.pk)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class UserListView(generics.ListAPIView):
    authentication_classes = (JWTAuthentication,)
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)

    @swagger_auto_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.select_related("organization").order_by("-created_at")
