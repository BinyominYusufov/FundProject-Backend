from __future__ import annotations

from rest_framework import serializers

from campaigns.models import Campaign
from donations.models import Donation


class DonationSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    donor_username = serializers.CharField(source="user.username", read_only=True)
    donor_email = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "user",
            "donor_username",
            "donor_email",
            "campaign",
            "campaign_name",
            "created_at",
        )
        read_only_fields = ("id", "user", "created_at")

    def get_donor_email(self, obj):
        return obj.user.email or ""


class AdminDonationSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    organization_name = serializers.CharField(source="campaign.organization.name", read_only=True)
    donor_username = serializers.CharField(source="user.username", read_only=True)
    donor_email = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "user",
            "donor_username",
            "donor_email",
            "campaign",
            "campaign_name",
            "organization_name",
            "created_at",
        )
        read_only_fields = fields

    def get_donor_email(self, obj):
        return obj.user.email or ""


class DonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ("campaign", "amount")

    def validate_amount(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_campaign(self, value: Campaign) -> Campaign:
        return value

    def create(self, validated_data: dict) -> Donation:
        from config.dev_auth import ensure_dev_entities, get_dev_user
        request = self.context.get("request")
        user = get_dev_user(request) if request is not None else None
        if user is None:
            user, _ = ensure_dev_entities()
        if user is None:
            raise serializers.ValidationError(
                "Bootstrap failed: run `python manage.py migrate` first.",
            )
        if getattr(user, "is_blocked", False) or not user.is_active:
            raise serializers.ValidationError("Account is not allowed to donate.")
        validated_data["user"] = user
        return super().create(validated_data)
