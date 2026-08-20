from rest_framework import serializers

from src.apps.documents.models import DocumentReviewStatus, DocumentVersion


class DocumentUploadSerializer(serializers.Serializer):
    document_pubkey = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.CharField(max_length=32)
    storage_key = serializers.CharField(max_length=2000)
    mime_type = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=0)
    checksum = serializers.CharField(required=False, allow_blank=True)


class DocumentRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=2000, allow_blank=False)


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = (
            "id", "version_number", "document_type", "status", "storage_key",
            "mime_type", "file_size", "checksum", "is_active", "reviewer",
            "reviewed_at", "rejection_reason", "created_at",
        )
        read_only_fields = fields
