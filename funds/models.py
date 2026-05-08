from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models

from users.models import Organization


class Fund(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    class Category(models.TextChoices):
        EDUCATION = "education", "Education"
        HEALTH = "health", "Health"
        ENVIRONMENT = "environment", "Environment"
        COMMUNITY = "community", "Community"
        EMERGENCY = "emergency", "Emergency"
        ANIMALS = "animals", "Animals"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255)
    description = models.TextField()
    goal_amount = models.PositiveBigIntegerField()
    raised_amount = models.PositiveBigIntegerField(default=0)
    category = models.CharField(max_length=32, choices=Category.choices, db_index=True)

    country = models.CharField(max_length=128)
    city = models.CharField(max_length=128)
    address = models.CharField(max_length=512)

    cover_image = models.ImageField(upload_to="funds/covers/%Y/%m/")
    supporting_document = models.FileField(upload_to="funds/documents/%Y/%m/")

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    rejection_reason = models.TextField(blank=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="funds",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_funds",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=("organization", "status")),
        ]

    def __str__(self) -> str:
        return self.title
