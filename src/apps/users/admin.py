from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # `role` retiré : n'existe plus sur ce modèle (RBAC = source unique de
    # vérité, consultable via l'admin de `authorization` / AUTH_USER_ROLES).
    list_display = ("id", "pubkey", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("pubkey", "email")
    readonly_fields = ("created_at", "updated_at")
    exclude = ("password",)
