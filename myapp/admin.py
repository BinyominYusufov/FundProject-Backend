from django.contrib import admin

from myapp.models import FundOwnerApplication


@admin.register(FundOwnerApplication)
class FundOwnerApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "full_name", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("email", "full_name")
