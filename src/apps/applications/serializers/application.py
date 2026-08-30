from rest_framework import serializers

from src.apps.applications.models import Application


class SubmitApplicationSerializer(serializers.Serializer):
    master_pubkey = serializers.CharField()


class DecisionSerializer(serializers.Serializer):
    accept = serializers.BooleanField()
    motif = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class ApplicationMasterSummarySerializer(serializers.Serializer):
    pubkey = serializers.CharField()
    nom = serializers.CharField()
    universite = serializers.CharField()


class ApplicationSerializer(serializers.ModelSerializer):
    master = ApplicationMasterSummarySerializer(read_only=True)

    class Meta:
        model = Application
        fields = ("pubkey", "master", "niveau", "date_soumission", "score", "statut")
        read_only_fields = fields
