from __future__ import annotations

from django.contrib import admin

from donations.models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "donor_username",
        "campaign_name",
        "amount",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("campaign__name", "user__email", "user__username")
    raw_id_fields = ("user", "campaign")
    ordering = ("-created_at",)

    @admin.display(description="Donor", ordering="user__username")
    def donor_username(self, obj):
        return obj.user.username if obj.user_id else ""

    @admin.display(description="Campaign", ordering="campaign__name")
    def campaign_name(self, obj):
        return obj.campaign.name if obj.campaign_id else ""
