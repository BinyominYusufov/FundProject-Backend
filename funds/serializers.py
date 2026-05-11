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
        from config.dev_auth import (
            AUTO_BOOTSTRAP,
            _bootstrap_dev_entities,
            get_dev_organization,
            get_dev_user,
        )
        request = self.context["request"]
        # AUTH DISABLED FOR DEVELOPMENT MODE
        # In production (ENABLE_AUTH=true) these resolve from the authenticated JWT user.
        user = get_dev_user(request)
        organization = get_dev_organization(request)
        # AUTO-BOOTSTRAP FALLBACK: create minimum required entities if DB is empty
        if (organization is None or user is None) and AUTO_BOOTSTRAP:
            user, organization = _bootstrap_dev_entities()
        if organization is None or user is None:
            raise serializers.ValidationError(
                {"detail": "At least one Organization and one User must exist in the database."},
            )
        return Fund.objects.create(
            organization=organization,
            created_by=user,
            status=Fund.Status.PENDING,
            raised_amount=0,
            **validated_data,
        )


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

    def update(self, instance: Fund, validated_data: dict[str, Any]) -> Fund:
        if "cover_image" in validated_data and validated_data["cover_image"] is None:
            validated_data.pop("cover_image")
        if "supporting_document" in validated_data and validated_data["supporting_document"] is None:
            validated_data.pop("supporting_document")
        return super().update(instance, validated_data)
