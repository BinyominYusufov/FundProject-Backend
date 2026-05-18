from django.contrib import admin

from funds.models import Fund


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "status",
        "category",
        "goal_amount",
        "raised_amount",
        "created_at",
    )
    list_filter = ("status", "category")
    search_fields = ("title",)
    readonly_fields = ("created_at", "updated_at", "raised_amount")
