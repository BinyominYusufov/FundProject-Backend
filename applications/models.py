from __future__ import annotations

from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models


class FundApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                r"^\+?[1-9]\d{6,14}$",
                message="Phone must be E.164-like (+ and 7-15 digits).",
            )
        ],
    )
    fund_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.fund_name} ({self.email})"
