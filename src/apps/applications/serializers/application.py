from rest_framework import serializers

from src.apps.applications.models import Application


class SubmitApplicationSerializer(serializers.Serializer):
    master_pubkey = serializers.CharField(required=False)
    masterId = serializers.CharField(required=False)
    master_id = serializers.CharField(required=False)

    def validate(self, attrs):
        pubkey = attrs.get("master_pubkey") or attrs.get("masterId") or attrs.get("master_id")
        if not pubkey:
            raise serializers.ValidationError({"master_pubkey": "L'identifiant du Master est obligatoire."})
        return {"master_pubkey": pubkey}


class DecisionSerializer(serializers.Serializer):
    accept = serializers.BooleanField()
    motif = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class ApplicationMasterSummarySerializer(serializers.Serializer):
    pubkey = serializers.CharField()
    nom = serializers.CharField()
    universite = serializers.CharField()


class ApplicationCandidateSummarySerializer(serializers.Serializer):
    pubkey = serializers.CharField()
    nom = serializers.CharField()
    prenom = serializers.CharField()
    cin = serializers.CharField()
    email = serializers.CharField()


class ApplicationSerializer(serializers.ModelSerializer):
    master = ApplicationMasterSummarySerializer(read_only=True)
    candidate_profile = ApplicationCandidateSummarySerializer(read_only=True)

    class Meta:
        model = Application
        fields = ("pubkey", "master", "candidate_profile", "niveau", "date_soumission", "score", "statut")
        read_only_fields = fields
