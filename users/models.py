from __future__ import annotations

import re
from typing import Any, ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, UniqueConstraint


class Organization(models.Model):
    name = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager["User"]):
    def create_user(
        self,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        if not username:
            raise ValueError("username must be set")
        username = username.strip().lower()
        if not username:
            raise ValueError("username must be set")
        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_blocked", False)
        extra_fields.setdefault("name", "Administrator")
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        FUND_OWNER = "fund_owner", "Fund owner"

    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=32, choices=Role.choices, db_index=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["name"]

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)
        constraints: ClassVar[list[UniqueConstraint]] = [
            UniqueConstraint(
                fields=("email",),
                condition=Q(email__isnull=False) & ~Q(email=""),
                name="users_user_email_when_set_uniq",
            ),
        ]

    def __str__(self) -> str:
        return self.username

    def get_full_name(self) -> str:
        return self.name.strip() if self.name else ""


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class Donation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    amount = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.COMPLETED,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations",
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="donations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.amount} -> {self.campaign_id}"


def unique_username_from_email_hint(email: str, *, UserModel: type[User] | None = None) -> str:
    """Сгенерировать уникальный username из локальной части email (для заявок и миграций)."""
    UserModel = UserModel or User
    local = (email or "user").split("@")[0].strip() or "user"
    base = re.sub(r"[^\w\-.]", "_", local, flags=re.UNICODE)[:100].strip("_") or "user"
    candidate = base
    n = 0
    while UserModel.objects.filter(username__iexact=candidate.lower()).exists():
        n += 1
        candidate = f"{base}{n}"
    return candidate.lower()
