from __future__ import annotations

from django.contrib.auth.models import Group
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as JWTTokenRefreshView

from config.dev_auth import ENABLE_AUTH, get_dev_user
from users.models import User
from users.permissions import IsAuthenticatedActiveUser
from users.serializers import UserSerializer

from myapp.permissions import FUNOWNERS_GROUP

from auth_app.services import change_user_password
# from auth_app.throttles import ChangePasswordThrottle, LoginThrottle, RegisterThrottle

from .serializers import (
    ChangePasswordErrorSerializer,
    ChangePasswordSerializer,
    ChangePasswordSuccessSerializer,
    CustomTokenObtainPairSerializer,
    DetailSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutBodySerializer,
    LogoutSuccessSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    # throttle_classes = (RegisterThrottle,)
    throttle_classes = ()

    @swagger_auto_schema(
        tags=['Auth'],
        request_body=RegisterSerializer,
        responses={201: RegisterResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()
        if user.role == User.Role.FUND_OWNER:
            group, _ = Group.objects.get_or_create(name=FUNOWNERS_GROUP)
            user.groups.add(group)
        refresh: RefreshToken = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer
    # throttle_classes = (LoginThrottle,)
    throttle_classes = ()

    @swagger_auto_schema(
        tags=['Auth'],
        request_body=LoginSerializer,
        responses={200: LoginResponseSerializer},
    )
    def post(self, request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(
            {
                "user": UserSerializer(data["user"]).data,
                "tokens": {
                    "access": data["access"],
                    "refresh": data["refresh"],
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    # Production: authentication_classes = (JWTAuthentication,), permission_classes = (IsAuthenticatedActiveUser,)
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)

    @swagger_auto_schema(
        tags=['Auth'],
        request_body=LogoutBodySerializer,
        responses={200: LogoutSuccessSerializer, 400: DetailSerializer, 403: DetailSerializer},
    )
    def post(self, request) -> Response:
        body = LogoutBodySerializer(data=request.data)
        body.is_valid(raise_exception=True)
        refresh_token: str = body.validated_data["refresh"]
        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        claim = api_settings.USER_ID_CLAIM
        try:
            token_uid = int(token[claim])
        except (KeyError, TypeError, ValueError):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.user.is_authenticated and token_uid != request.user.pk:
            return Response(
                {"detail": "Refresh token does not match the authenticated user."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    # AUTH DISABLED FOR DEVELOPMENT MODE
    # Production: authentication_classes = (JWTAuthentication,), permission_classes = (IsAuthenticatedActiveUser,)
    authentication_classes = () if not ENABLE_AUTH else (JWTAuthentication,)
    permission_classes = (permissions.AllowAny,) if not ENABLE_AUTH else (IsAuthenticatedActiveUser,)
    throttle_classes = ()

    @swagger_auto_schema(
        tags=["Auth"],
        request_body=ChangePasswordSerializer,
        responses={
            200: ChangePasswordSuccessSerializer,
            400: ChangePasswordErrorSerializer,
            429: DetailSerializer,
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        # AUTH DISABLED FOR DEVELOPMENT MODE — falls back to first DB user when not authenticated
        target_user = get_dev_user(request)
        if target_user is None:
            return Response(
                {"error": "No user in database.", "code": "PASSWORD_CHANGE_FAILED"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request, "password_target_user": target_user},
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                {"error": "Could not update password.", "code": "PASSWORD_CHANGE_FAILED"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        change_user_password(target_user, serializer.validated_data["new_password"])
        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshView(JWTTokenRefreshView):
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=['Auth'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
