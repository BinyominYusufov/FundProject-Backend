from django.contrib import admin

from ambassadors.models import Ambassador, AmbassadorApplication


@admin.register(AmbassadorApplication)
class AmbassadorApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "profession", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name", "email", "profession", "organization")


@admin.register(Ambassador)
class AmbassadorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "role", "is_featured", "is_active", "created_at")
    list_filter = ("is_featured", "is_active")
    search_fields = ("name", "role")
