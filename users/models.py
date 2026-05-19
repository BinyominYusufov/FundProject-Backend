from __future__ import annotations

import re
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q, UniqueConstraint


class Organization(models.Model):
    name = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)

    # Organization profile (fund-owner onboarding). A fund owner must complete
    # all of these before they are allowed to create funds. See
    # `missing_profile_fields` / `is_profile_complete` below.
    logo = models.ImageField(
        upload_to="organizations/logos/%Y/%m/",
        blank=True,
        null=True,
    )
    phone_number = models.CharField(max_length=32, blank=True, default="")
    description = models.TextField(blank=True, default="")
    country = models.CharField(max_length=128, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    address = models.CharField(max_length=512, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    # Profile-field keys, in display order, used by the onboarding flow.
    PROFILE_FIELDS: ClassVar[tuple[str, ...]] = (
        "logo",
        "name",
        "phone_number",
        "description",
        "country",
        "city",
        "address",
        "verification_documents",
    )

    @property
    def missing_profile_fields(self) -> list[str]:
        """Required onboarding fields that are still empty.

        An empty list means the organization profile is complete and the
        fund owner may create funds.
        """
        missing: list[str] = []
        if not self.logo:
            missing.append("logo")
        if not (self.name or "").strip():
            missing.append("name")
        if not (self.phone_number or "").strip():
            missing.append("phone_number")
        if not (self.description or "").strip():
            missing.append("description")
        if not (self.country or "").strip():
            missing.append("country")
        if not (self.city or "").strip():
            missing.append("city")
        if not (self.address or "").strip():
            missing.append("address")
        # `documents` is the reverse relation from OrganizationDocument.
        if self.pk is None or not self.documents.exists():
            missing.append("verification_documents")
        return missing

    @property
    def is_profile_complete(self) -> bool:
        return not self.missing_profile_fields


class OrganizationDocument(models.Model):
    """A verification document uploaded as part of organization onboarding.

    An organization may have several (registration, license, ID, …); at least
    one is required for the profile to count as complete.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="organizations/documents/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[tuple[str, ...]] = ("-uploaded_at",)

    def __str__(self) -> str:
        return f"Document #{self.pk} for org {self.organization_id}"


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
        DONOR = "donor", "Donor"

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
