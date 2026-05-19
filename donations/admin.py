from django.contrib import admin

from donations.models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "fund", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("fund__title", "user__username", "user__email")
    raw_id_fields = ("fund", "user")
