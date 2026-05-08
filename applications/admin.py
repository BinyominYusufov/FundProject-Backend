from __future__ import annotations

from django.contrib import admin

from applications.models import FundApplication


@admin.register(FundApplication)
class FundApplicationAdmin(admin.ModelAdmin):
    list_display = ("fund_name", "name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("fund_name", "name", "email", "phone")
    ordering = ("-created_at",)
