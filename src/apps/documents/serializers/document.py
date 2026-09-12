from rest_framework import serializers


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    slot_type = serializers.CharField(min_length=2, max_length=32)
    domaine = serializers.CharField(required=False, allow_blank=True, default="")
    annee_licence = serializers.CharField(required=False, allow_blank=True, default="")
    redoublement_annee = serializers.CharField(required=False, allow_blank=True, default="")
    justificatif_index = serializers.IntegerField(required=False, min_value=0, default=0)


class DocumentRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)


class DocumentVersionSerializer(serializers.Serializer):
    pubkey = serializers.CharField()
    version_number = serializers.IntegerField()
    status = serializers.CharField()
    is_active = serializers.BooleanField()
    mime_type = serializers.CharField()
    file_size = serializers.IntegerField()
    checksum = serializers.CharField()
    rejection_reason = serializers.CharField(allow_null=True)
    reviewed_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()
    slot_pubkey = serializers.SerializerMethodField()
    slot_type = serializers.SerializerMethodField()
    domaine = serializers.SerializerMethodField()
    annee_licence = serializers.SerializerMethodField()
    redoublement_annee = serializers.SerializerMethodField()
    justificatif_index = serializers.SerializerMethodField()
    candidate_profile_pubkey = serializers.SerializerMethodField()
    reviewer_email = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    def get_slot_pubkey(self, obj): return obj.slot.pubkey
    def get_slot_type(self, obj): return obj.slot.type
    def get_domaine(self, obj): return obj.slot.domaine
    def get_annee_licence(self, obj): return obj.slot.annee_licence
    def get_redoublement_annee(self, obj): return obj.slot.redoublement_annee
    def get_justificatif_index(self, obj): return obj.slot.justificatif_index
    def get_candidate_profile_pubkey(self, obj): return obj.slot.candidate_profile.pubkey
    def get_reviewer_email(self, obj): return obj.reviewer.email if obj.reviewer_id else None

    def get_download_url(self, obj):
        # Jamais généré dans les vues LISTE — cf. context["include_download_url"].
        if not self.context.get("include_download_url"):
            return None
        storage = self.context.get("storage")
        if storage is None or not obj.storage_key:
            return None
        return storage.signed_url(obj.storage_key)


class DocumentSlotSerializer(serializers.Serializer):
    """Vue "slot" : utile pour le récapitulatif front (un slot par pièce
    attendue, avec sa version courante et son statut)."""

    pubkey = serializers.CharField()
    type = serializers.CharField()
    domaine = serializers.CharField()
    annee_licence = serializers.CharField()
    redoublement_annee = serializers.CharField()
    justificatif_index = serializers.IntegerField()
    current_version = serializers.SerializerMethodField()

    def get_current_version(self, obj):
        active = next((v for v in obj.versions.all() if v.is_active and v.deleted_at is None), None)
        if active is None:
            return None
        return DocumentVersionSerializer(active, context=self.context).data