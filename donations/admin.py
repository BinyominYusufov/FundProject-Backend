from __future__ import annotations

from django.contrib import admin

from donations.models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "campaign",
        "amount",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("campaign__name", "user__email", "user__username")
    raw_id_fields = ("user", "campaign")
    ordering = ("-created_at",)
