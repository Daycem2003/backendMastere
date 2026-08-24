from django.contrib import admin

from .models import NotificationRecord


@admin.register(NotificationRecord)
class NotificationRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "candidate_profile", "application", "motif", "envoyee_le", "lu_le")
    list_filter = ("motif",)
    search_fields = ("pubkey", "candidate_profile__pubkey", "application__pubkey")
    readonly_fields = ("envoyee_le", "created_at")
