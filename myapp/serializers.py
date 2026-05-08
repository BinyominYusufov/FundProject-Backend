from __future__ import annotations

from rest_framework import serializers

from myapp.models import FundOwnerApplication


class FundOwnerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundOwnerApplication
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "description",
            "status",
            "created_at",
            "reviewed_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "reviewed_at",
        )

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        existing = FundOwnerApplication.objects.filter(email__iexact=value).first()
        if existing is None:
            return value
        if existing.status in (
            FundOwnerApplication.Status.PENDING,
            FundOwnerApplication.Status.APPROVED,
        ):
            raise serializers.ValidationError(
                "An application with this email is already pending or approved.",
            )
        raise serializers.ValidationError(
            "An application with this email already exists.",
        )


class FundOwnerApplicationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "reject"))
