from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "verified", "created_at")
    list_filter = ("verified",)
    search_fields = ("name",)


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "name",
            "role",
            "organization",
            "is_staff",
            "is_superuser",
            "is_active",
            "is_verified",
            "is_blocked",
        )

    def clean_username(self):
        v = (self.cleaned_data.get("username") or "").strip().lower()
        if not v:
            raise forms.ValidationError("Username is required.")
        return v

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text="Use the link below to change the password.",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "name",
            "role",
            "organization",
            "is_active",
            "is_verified",
            "is_blocked",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    ordering = ("-created_at",)
    list_display = (
        "username",
        "email",
        "name",
        "role",
        "organization",
        "is_staff",
        "is_active",
        "is_verified",
        "is_blocked",
        "created_at",
    )
    list_filter = ("role", "is_staff", "is_active", "is_verified", "is_blocked")
    search_fields = ("username", "email", "name")
    readonly_fields = ("created_at", "last_login")
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Profile", {"fields": ("name", "role", "organization", "is_verified", "is_blocked")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "name",
                    "role",
                    "organization",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "is_verified",
                    "is_blocked",
                ),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")
