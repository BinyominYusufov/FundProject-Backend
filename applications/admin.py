from __future__ import annotations

from django.contrib import admin

from applications.models import FundApplication


@admin.register(FundApplication)
class FundApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "fund_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("fund_name", "name", "email", "phone")
    ordering = ("-created_at",)
    actions = ("admin_approve", "admin_reject")

    @admin.action(description="Approve selected applications")
    def admin_approve(self, request, queryset):
        queryset.update(status=FundApplication.Status.APPROVED)

    @admin.action(description="Reject selected applications")
    def admin_reject(self, request, queryset):
        queryset.update(status=FundApplication.Status.REJECTED)
