from rest_framework import serializers

from src.apps.documents.models import DocumentVersion


class DocumentUploadSerializer(serializers.Serializer):
    """FIX: le client envoie désormais un vrai fichier (`file`), plus des
    métadonnées déclaratives (storage_key/mime_type/file_size/checksum).
    Ces dernières sont calculées côté serveur dans DocumentUploadView."""

    document_pubkey = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.CharField(max_length=32)
    file = serializers.FileField()


class DocumentRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=2000, allow_blank=False)


class DocumentVersionSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = (
            "pubkey", "version_number", "document_type", "status",
            "mime_type", "file_size", "checksum", "is_active", "reviewer",
            "reviewed_at", "rejection_reason", "created_at", "download_url",
        )
        # FIX: `pubkey` exposé (absent avant), `storage_key` retiré de la
        # sortie publique (c'est un détail d'implémentation du backend de
        # stockage, pas une donnée à exposer telle quelle au client — on
        # expose à la place une URL signée via `download_url`).
        read_only_fields = fields

    def get_download_url(self, obj) -> str | None:
        storage = self.context.get("storage")
        if storage is None or not obj.storage_key:
            return None
        return storage.signed_url(obj.storage_key)
