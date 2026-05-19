from __future__ import annotations

from rest_framework import serializers

from ambassadors.models import Ambassador, AmbassadorApplication


class AmbassadorApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbassadorApplication
        fields = (
            "full_name",
            "email",
            "phone",
            "profession",
            "organization",
            "message",
        )
        extra_kwargs = {
            "organization": {"required": False, "allow_null": True, "allow_blank": True},
            "message": {"required": False, "allow_null": True, "allow_blank": True},
        }


class AmbassadorApplicationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmbassadorApplication
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "profession",
            "organization",
            "message",
            "status",
            "created_at",
        )
        read_only_fields = fields


class AmbassadorCreateSerializer(serializers.ModelSerializer):
    # Declared explicitly so an omitted boolean in multipart/form-data falls
    # back to the model default (True/False) instead of DRF's HTML-form
    # "missing checkbox => False" coercion.
    is_featured = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Ambassador
        fields = (
            "name",
            "role",
            "image",
            "description",
            "instagram_url",
            "twitter_url",
            "linkedin_url",
            "is_featured",
            "is_active",
        )
        extra_kwargs = {
            "image": {"required": False, "allow_null": True},
            "description": {"required": False, "allow_null": True, "allow_blank": True},
            "instagram_url": {"required": False, "allow_null": True, "allow_blank": True},
            "twitter_url": {"required": False, "allow_null": True, "allow_blank": True},
            "linkedin_url": {"required": False, "allow_null": True, "allow_blank": True},
        }


class AmbassadorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambassador
        fields = (
            "name",
            "role",
            "image",
            "description",
            "instagram_url",
            "twitter_url",
            "linkedin_url",
            "is_featured",
            "is_active",
        )
        extra_kwargs = {f: {"required": False} for f in fields}


class AmbassadorResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambassador
        fields = (
            "id",
            "name",
            "role",
            "image",
            "description",
            "instagram_url",
            "twitter_url",
            "linkedin_url",
            "is_featured",
            "is_active",
            "created_at",
        )
        read_only_fields = fields
