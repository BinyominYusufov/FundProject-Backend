from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from myapp.permissions import IsAdminRole
from .models import User
# from .permissions import IsAuthenticatedActiveUser
from .serializers import UserSerializer, UserUpdateSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticatedActiveUser,)
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

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
        # DEV: без логина — первый пользователь
        u = self.request.user
        if u.is_authenticated:
            return User.objects.select_related("organization").get(pk=u.pk)
        first = User.objects.select_related("organization").order_by("pk").first()
        if first is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("No users in database.")
        return first

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class UserListView(generics.ListAPIView):
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    @swagger_auto_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.select_related("organization").order_by("-created_at")
