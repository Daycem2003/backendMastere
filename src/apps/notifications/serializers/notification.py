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

    class Meta:
        model = NotificationRecord
        fields = (
            "pubkey", "motif", "document_concerne", "objet", "corps",
            "application_pubkey", "envoyee_le", "is_read",
        )
        read_only_fields = fields

    def get_is_read(self, obj) -> bool:
        return obj.lu_le is not None


class BroadcastNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        from src.apps.notifications.models import BroadcastNotification
        model = BroadcastNotification
        fields = ("pubkey", "cible", "objet", "message", "envoyee_le", "created_at")
        read_only_fields = fields


class CreateBroadcastNotificationSerializer(serializers.Serializer):
    cible = serializers.ChoiceField(choices=["COORDINATEURS", "CANDIDATS", "TOUS"], default="TOUS")
    objet = serializers.CharField(max_length=255)
    message = serializers.CharField(max_length=5000)

