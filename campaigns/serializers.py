from __future__ import annotations

from rest_framework import serializers

from users.models import Organization, User

from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "organization",
            "organization_name",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class AdminCampaignSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "organization",
            "organization_name",
            "created_at",
        )
        read_only_fields = fields


class FundOwnerCampaignSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "organization",
            "organization_name",
            "created_at",
        )
        read_only_fields = ("id", "organization", "organization_name", "created_at")


class FundOwnerCampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ("name",)

    def validate_name(self, value: str) -> str:
        v = value.strip()
        if not v:
            raise serializers.ValidationError("Cannot be blank.")
        if len(v) > 255:
            raise serializers.ValidationError("Max 255 characters.")
        return v

    def create(self, validated_data: dict) -> Campaign:
        request = self.context["request"]
        user: User | None = request.user if request.user.is_authenticated else None
        organization = user.organization if user else None
        # DEV: без логина — первая организация
        if organization is None:
            organization = Organization.objects.order_by("pk").first()
        if organization is None:
            raise serializers.ValidationError(
                "DEV: создай Organization в БД или войди под fund owner с organization.",
            )
        # Продакшен:
        # organization = user.organization
        # if organization is None:
        #     raise serializers.ValidationError("No organization assigned to your account.")
        validated_data["organization"] = organization
        return super().create(validated_data)
