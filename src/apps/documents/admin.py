from django.contrib import admin

from .models import DocumentAuditEvent, DocumentVersion


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_profile", "document_type", "version_number", "status", "is_active")
    list_filter = ("status", "document_type", "is_active")
    search_fields = ("storage_key", "checksum", "candidate_profile__pubkey")
    readonly_fields = ("created_at", "reviewed_at")


@admin.register(DocumentAuditEvent)
class DocumentAuditEventAdmin(admin.ModelAdmin):
    list_display = ("id", "document_version", "action", "actor", "created_at")
    list_filter = ("action",)
    readonly_fields = ("created_at",)
