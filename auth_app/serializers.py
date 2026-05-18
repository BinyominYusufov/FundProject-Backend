from __future__ import annotations

from django.contrib.auth import authenticate
from myapp.permissions import FUNOWNERS_GROUP
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Organization, User
from users.serializers import UserSerializer


class RegisterSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
    )
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password_confirm = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "name",
            "password",
            "password_confirm",
            "role",
            "organization",
        )

    def validate_username(self, value: str) -> str:
        v = (value or "").strip().lower()
        if not v:
            raise serializers.ValidationError("Username is required.")
        if len(v) > 150:
            raise serializers.ValidationError("Max 150 characters.")
        if User.objects.filter(username=v).exists():
            raise serializers.ValidationError("This username is already taken.")
        return v

    def validate_email(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        e = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=e).exists():
            raise serializers.ValidationError("This email is already in use.")
        return e

    def validate_name(self, value: str) -> str:
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Name is required.")
        if len(v) > 255:
            raise serializers.ValidationError("Max 255 characters.")
        return v

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        role = attrs["role"]
        if role == User.Role.ADMIN and attrs.get("organization") is not None:
            raise serializers.ValidationError({"organization": "Must be empty for admin role."})
        if role == User.Role.DONOR and attrs.get("organization") is not None:
            raise serializers.ValidationError({"organization": "Must be empty for donor role."})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        role = validated_data.get("role")
        if role == User.Role.FUND_OWNER and validated_data.get("organization") is None:
            username = validated_data.get("username") or "owner"
            validated_data["organization"] = Organization.objects.create(
                name=f"{username}'s Organization",
                verified=True,
            )
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Login with unique `username` and `password` (регистр логина не важен)."""

    username = serializers.CharField(
        required=True,
        allow_blank=False,
        write_only=True,
        max_length=150,
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        max_length=128,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict) -> dict:
        uname = (attrs.get("username") or "").strip().lower()
        if not uname:
            raise serializers.ValidationError({"username": "This field may not be blank."})
        password: str = attrs["password"]

        if not User.objects.filter(username=uname).exists():
            raise serializers.ValidationError({"detail": "Invalid username or password."})

        user = authenticate(
            request=self.context.get("request"),
            username=uname,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError({"detail": "Invalid username or password."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account is disabled."})

        if getattr(user, "is_blocked", False):
            raise serializers.ValidationError({"detail": "Account is blocked."})

        refresh: RefreshToken = RefreshToken.for_user(user)

        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class AuthTokensSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    tokens = AuthTokensSerializer(read_only=True)


class RegisterResponseSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    tokens = AuthTokensSerializer(read_only=True)


class LogoutBodySerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, max_length=512)


class LogoutSuccessSerializer(serializers.Serializer):
    message = serializers.CharField()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, max_length=128)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    confirm_password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    def validate(self, attrs: dict) -> dict:
        user: User = self.context.get("password_target_user") or self.context["request"].user
        if not user.is_authenticated:
            raise serializers.ValidationError("invalid")
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("invalid")
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("invalid")
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError("invalid")
        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError("invalid")
        return attrs


class ChangePasswordSuccessSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChangePasswordErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    code = serializers.CharField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT with role + profile fields in body; token claims include `role`."""

    @staticmethod
    def _role_key(user: User) -> str:
        if user.is_staff:
            return "admin"
        if user.groups.filter(name=FUNOWNERS_GROUP).exists() or user.role == User.Role.FUND_OWNER:
            return "fund_owner"
        return "user"

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["role"] = cls._role_key(user)
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        u: User = self.user
        data["role"] = self._role_key(u)
        data["email"] = u.email or ""
        data["full_name"] = u.get_full_name()
        return data
