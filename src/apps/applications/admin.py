from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "candidate_profile", "master", "niveau", "statut", "score", "date_soumission")
    list_filter = ("statut", "niveau")
    search_fields = ("pubkey", "candidate_profile__pubkey", "master__pubkey")
    readonly_fields = ("date_soumission", "created_at")
