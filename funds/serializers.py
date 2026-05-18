from __future__ import annotations

from typing import Any

from rest_framework import serializers

from funds.models import Fund
from funds.validators import (
    validate_cover_image_file,
    validate_supporting_document_file,
)


class FundReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fund
        fields = (
            "id",
            "title",
            "description",
            "goal_amount",
            "raised_amount",
            "category",
            "country",
            "city",
            "address",
            "cover_image",
            "supporting_document",
            "status",
            "rejection_reason",
            "organization_id",
            "created_by_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class FundCreateSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(validators=[validate_cover_image_file])
    supporting_document = serializers.FileField(validators=[validate_supporting_document_file])

    class Meta:
        model = Fund
        fields = (
            "title",
            "description",
            "goal_amount",
            "category",
            "country",
            "city",
            "address",
            "cover_image",
            "supporting_document",
        )

    def validate_goal_amount(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Goal amount must be greater than zero.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Fund:
        from users.models import Organization
        request = self.context["request"]
        user = request.user
        if not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError({"detail": "Authentication required."})
        organization = getattr(user, "organization", None)
        if organization is None:
            organization = Organization.objects.create(
                name=f"{user.username}'s Organization",
                verified=False,
            )
            user.organization = organization
            user.save(update_fields=["organization"])
        # Unverified organizations may only create draft funds; a verified
        # organization submits the fund for admin review (pending).
        status = Fund.Status.PENDING if organization.verified else Fund.Status.DRAFT
        return Fund.objects.create(
            organization=organization,
            created_by=user,
            status=status,
            raised_amount=0,
            **validated_data,
        )


FUND_OWNER_ALLOWED_STATUSES = frozenset({Fund.Status.DRAFT, Fund.Status.PAUSED})


class FundPartialUpdateSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(
        validators=[validate_cover_image_file],
        required=False,
        allow_null=True,
    )
    supporting_document = serializers.FileField(
        validators=[validate_supporting_document_file],
        required=False,
        allow_null=True,
    )
    status = serializers.ChoiceField(choices=Fund.Status.choices, required=False)

    class Meta:
        model = Fund
        fields = (
            "title",
            "description",
            "goal_amount",
            "category",
            "country",
            "city",
            "address",
            "cover_image",
            "supporting_document",
            "status",
        )

    def validate_goal_amount(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Goal amount must be greater than zero.")
        return value

    def validate_status(self, value: str) -> str:
        request = self.context.get("request")
        user = getattr(request, "user", None) if request is not None else None
        if user is None or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("Authentication required.")
        if user.is_staff:
            return value
        # Fund owners may only move a fund into draft or paused.
        if value not in FUND_OWNER_ALLOWED_STATUSES:
            raise serializers.ValidationError(
                "Fund owners may only set status to 'draft' or 'paused'.",
            )
        return value

    def update(self, instance: Fund, validated_data: dict[str, Any]) -> Fund:
        if "cover_image" in validated_data and validated_data["cover_image"] is None:
            validated_data.pop("cover_image")
        if "supporting_document" in validated_data and validated_data["supporting_document"] is None:
            validated_data.pop("supporting_document")
        return super().update(instance, validated_data)
