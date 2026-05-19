from __future__ import annotations

from typing import ClassVar

from django.db import models


class AmbassadorApplication(models.Model):
    """Public application to become an ambassador (awaiting moderation)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    full_name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=32)
    profession = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ambassador_applications"
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}> ({self.status})"


class Ambassador(models.Model):
    """A published ambassador shown on the public site."""

    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="ambassadors/%Y/%m/",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True, null=True)
    instagram_url = models.URLField(max_length=500, blank=True, null=True)
    twitter_url = models.URLField(max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ambassadors"
        ordering: ClassVar[tuple[str, ...]] = ("-is_featured", "-created_at")

    def __str__(self) -> str:
        return f"{self.name} — {self.role}"
