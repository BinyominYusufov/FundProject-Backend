from __future__ import annotations

from typing import Any

from rest_framework import serializers

from funds.validators import (
    validate_cover_image_file,
    validate_supporting_document_file,
)
from users.models import Organization, OrganizationDocument


class OrganizationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationDocument
        fields = ("id", "file", "uploaded_at")
        read_only_fields = fields


class OrganizationPublicSerializer(serializers.ModelSerializer):
    """Read serializer for `GET /api/fund-owner/profile/`.

    Drives the onboarding flow: the frontend uses `profile_complete` /
    `missing_fields` / `can_create_fund` to decide whether to redirect the
    fund owner to Settings → Organization Profile and gate fund creation.
    """

    documents = OrganizationDocumentSerializer(many=True, read_only=True)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete",
        read_only=True,
    )
    missing_fields = serializers.ListField(
        source="missing_profile_fields",
        child=serializers.CharField(),
        read_only=True,
    )
    can_create_fund = serializers.SerializerMethodField()
    can_publish_fund = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "logo",
            "phone_number",
            "description",
            "country",
            "city",
            "address",
            "documents",
            "verified",
            "profile_complete",
            "missing_fields",
            "can_create_fund",
            "can_publish_fund",
            "created_at",
        )
        read_only_fields = fields

    def get_can_create_fund(self, obj: Organization) -> bool:
        # Profile must be complete to create a fund (draft or otherwise).
        return obj.is_profile_complete

    def get_can_publish_fund(self, obj: Organization) -> bool:
        # Publishing/activating additionally requires a verified organization.
        return obj.is_profile_complete and obj.verified


class OrganizationWriteSerializer(serializers.ModelSerializer):
    """Write serializer for `PATCH /api/fund-owner/profile/` (multipart).

    `documents` is a write-only list of uploaded files; each one is appended
    as a new OrganizationDocument (existing documents are kept).
    """

    logo = serializers.ImageField(
        validators=[validate_cover_image_file],
        required=False,
        allow_null=True,
    )
    documents = serializers.ListField(
        child=serializers.FileField(validators=[validate_supporting_document_file]),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Organization
        fields = (
            "name",
            "logo",
            "phone_number",
            "description",
            "country",
            "city",
            "address",
            "documents",
        )

    def validate_name(self, value: str) -> str:
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Organization name cannot be empty.")
        return v

    def update(self, instance: Organization, validated_data: dict[str, Any]) -> Organization:
        documents = validated_data.pop("documents", None)
        # Clearing the logo via an explicit null is allowed; omitting it keeps
        # the current logo (standard PATCH semantics).
        if "logo" in validated_data and validated_data["logo"] is None:
            validated_data.pop("logo")
        instance = super().update(instance, validated_data)
        if documents:
            OrganizationDocument.objects.bulk_create(
                [
                    OrganizationDocument(organization=instance, file=f)
                    for f in documents
                ],
            )
        return instance
