from __future__ import annotations

from rest_framework import serializers

from .models import Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "verified", "created_at")
        read_only_fields = ("id", "verified", "created_at")


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "name",
            "role",
            "organization",
            "is_active",
            "is_verified",
            "is_blocked",
            "created_at",
        )
        read_only_fields = (
            "id",
            "is_active",
            "is_verified",
            "is_blocked",
            "created_at",
        )


class AdminUserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "name",
            "role",
            "organization",
            "is_active",
            "is_verified",
            "is_blocked",
            "is_staff",
            "created_at",
        )
        read_only_fields = fields


class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "username",
            "email",
            "created_at",
            "is_verified",
            "is_blocked",
        )
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ("email", "username")

    def validate_username(self, value: str) -> str:
        v = (value or "").strip().lower()
        if not v:
            raise serializers.ValidationError("Invalid username.")
        qs = User.objects.filter(username=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return v

    def validate_email(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        e = User.objects.normalize_email(value)
        qs = User.objects.filter(email__iexact=e)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return e
