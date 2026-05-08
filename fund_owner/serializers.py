from __future__ import annotations

from rest_framework import serializers

from users.models import Organization


class OrganizationPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "verified", "created_at")
        read_only_fields = ("id", "name", "verified", "created_at")


class OrganizationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name",)
