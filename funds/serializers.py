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
        request = self.context["request"]
        user = request.user
        organization = user.organization
        if organization is None:
            raise serializers.ValidationError(
                {"organization": "No organization is assigned to your account."},
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
