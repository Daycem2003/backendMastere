from django.contrib import admin

from src.apps.users.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "pubkey",
        "email",
        "role",
        "is_active",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "role", "created_at")
    search_fields = ("pubkey", "email")
    readonly_fields = ("pubkey", "created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    @admin.display(boolean=True, description="Supprimé")
    def is_deleted(self, obj: User) -> bool:
        return obj.is_deleted


admin.site.register(User, UserAdmin)
