from __future__ import annotations

from rest_framework import serializers

from applications.models import FundApplication


class FundApplicationSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundApplication
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "fund_name",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at")


class AdminFundApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundApplication
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "fund_name",
            "status",
            "created_at",
        )
        read_only_fields = fields
