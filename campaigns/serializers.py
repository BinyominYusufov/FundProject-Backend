from __future__ import annotations

from rest_framework import serializers

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
        from config.dev_auth import ensure_dev_entities, get_dev_organization
        request = self.context["request"]
        organization = get_dev_organization(request)
        if organization is None:
            _, organization = ensure_dev_entities()
        if organization is None:
            raise serializers.ValidationError(
                "Bootstrap failed: run `python manage.py migrate` first.",
            )
        validated_data["organization"] = organization
        return super().create(validated_data)
