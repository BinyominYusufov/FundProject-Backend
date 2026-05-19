from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from donations.models import Donation


class DonationSerializer(serializers.ModelSerializer):
    """Read representation returned for create / list / retrieve."""

    class Meta:
        model = Donation
        fields = (
            "id",
            "amount",
            "fund",
            "user",
            "status",
            "created_at",
        )
        read_only_fields = fields


class DonationCreateSerializer(serializers.ModelSerializer):
    # `fund_id` in the body; `user` is never trusted from the client — it is
    # taken from request.user in the viewset.
    fund_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Donation
        fields = ("amount", "fund_id")

    def validate_amount(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value


class AdminDonationStatusSerializer(serializers.ModelSerializer):
    """Admin status transition: only `pending` -> `completed` | `failed`."""

    class Meta:
        model = Donation
        fields = ("status",)

    def validate_status(self, value: str) -> str:
        allowed_targets = {Donation.Status.COMPLETED, Donation.Status.FAILED}
        if value not in allowed_targets:
            raise serializers.ValidationError(
                "Status can only be changed to 'completed' or 'failed'.",
            )
        if self.instance is not None and self.instance.status != Donation.Status.PENDING:
            raise serializers.ValidationError(
                "Only pending donations can be updated.",
            )
        return value
