from rest_framework import serializers

from src.apps.notifications.models import NotificationMotif, NotificationRecord


class NotifyDocumentIssueSerializer(serializers.Serializer):
    candidate_profile_pubkey = serializers.CharField()
    application_pubkey = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    motif = serializers.ChoiceField(choices=NotificationMotif.choices)
    document_concerne = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    objet = serializers.CharField(max_length=255)
    corps = serializers.CharField(max_length=5000)


class NotificationRecordSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    application_pubkey = serializers.CharField(source="application.pubkey", default=None, read_only=True)
    piece_jointe_url = serializers.SerializerMethodField()

    class Meta:
        model = NotificationRecord
        fields = (
            "pubkey", "motif", "document_concerne", "objet", "corps",
            "piece_jointe_nom", "piece_jointe_url",
            "application_pubkey", "envoyee_le", "is_read",
        )
        read_only_fields = fields

    def get_is_read(self, obj) -> bool:
        return obj.lu_le is not None

    def get_piece_jointe_url(self, obj) -> str | None:
        if not getattr(obj, "piece_jointe_cle", None):
            return None
        try:
            from src.apps.documents.services.storage import get_default_storage
            return get_default_storage().signed_url(obj.piece_jointe_cle, expires_in=3600)
        except Exception:
            return None


class BroadcastNotificationSerializer(serializers.ModelSerializer):
    master_pubkey = serializers.CharField(source="master.pubkey", default=None, read_only=True)
    master_nom = serializers.CharField(source="master.nom", default=None, read_only=True)
    piece_jointe_url = serializers.SerializerMethodField()

    class Meta:
        from src.apps.notifications.models import BroadcastNotification
        model = BroadcastNotification
        fields = (
            "pubkey", "cible", "master_pubkey", "master_nom", "rang_max",
            "objet", "message", "piece_jointe_nom", "piece_jointe_url",
            "envoyee_le", "created_at",
        )
        read_only_fields = fields

    def get_piece_jointe_url(self, obj) -> str | None:
        if not getattr(obj, "piece_jointe_cle", None):
            return None
        try:
            from src.apps.documents.services.storage import get_default_storage
            return get_default_storage().signed_url(obj.piece_jointe_cle, expires_in=3600)
        except Exception:
            return None


class CreateBroadcastNotificationSerializer(serializers.Serializer):
    cible = serializers.ChoiceField(
        choices=["COORDINATEURS", "CANDIDATS", "TOUS", "MASTER_RANG"], default="TOUS"
    )
    objet = serializers.CharField(max_length=255)
    message = serializers.CharField(max_length=5000)
    master_pubkey = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    rang_max = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    piece_jointe = serializers.FileField(required=False, allow_null=True)


class NotifyTopRankedSerializer(serializers.Serializer):
    master_pubkey = serializers.CharField()
    n_premiers = serializers.IntegerField(min_value=1, default=10)
    objet = serializers.CharField(
        max_length=255,
        required=False,
        default="Appel au dépôt du dossier de candidature à l'administration de l'institut",
    )
    piece_jointe = serializers.FileField(required=False, allow_null=True)
    joindre_classement_csv = serializers.BooleanField(required=False, default=False)

