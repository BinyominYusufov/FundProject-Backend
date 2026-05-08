from __future__ import annotations

from django.contrib import admin

from campaigns.models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created_at")
    search_fields = ("name", "organization__name")
    ordering = ("-created_at",)
    raw_id_fields = ("organization",)
