from rest_framework import serializers

from src.apps.masters.models import Master
from src.apps.documents.models import RequiredDocument
from src.apps.scoring.models import ScoreCriterion, ScoreFormula


class CreateMasterSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=200)
    domaine = serializers.CharField(max_length=100)
    discipline = serializers.CharField(max_length=100)
    specialite = serializers.CharField(max_length=200)
    nombre_places = serializers.IntegerField(min_value=1)
    date_debut = serializers.DateTimeField()
    date_fin = serializers.DateTimeField()
    type_licence_pubkeys = serializers.ListField(child=serializers.CharField(), required=False)


class UpdateMasterSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=200, required=False)
    ville = serializers.CharField(max_length=100, required=False)
    nombre_places = serializers.IntegerField(min_value=1, required=False)
    date_debut = serializers.DateTimeField(required=False)
    date_fin = serializers.DateTimeField(required=False)


class SetAcceptedLicenceTypesSerializer(serializers.Serializer):
    type_licence_pubkeys = serializers.ListField(child=serializers.CharField())


class SetPasserellesSerializer(serializers.Serializer):
    from_master_pubkeys = serializers.ListField(child=serializers.CharField())


class AddRequiredDocumentSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=50)


class ScoreCriterionSerializer(serializers.Serializer):
    critere = serializers.CharField(max_length=100)
    poids = serializers.FloatField(min_value=0.001)


class SetScoreFormulaSerializer(serializers.Serializer):
    criteria = ScoreCriterionSerializer(many=True)


class TypeLicenceSummarySerializer(serializers.Serializer):
    pubkey = serializers.CharField()
    intitule = serializers.CharField()


class RequiredDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredDocument
        fields = ("pubkey", "type")
        read_only_fields = fields


class ScoreCriterionOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreCriterion
        fields = ("pubkey", "critere", "poids")
        read_only_fields = fields


class ScoreFormulaSerializer(serializers.ModelSerializer):
    criteria = ScoreCriterionOutSerializer(many=True, read_only=True)

    class Meta:
        model = ScoreFormula
        fields = ("pubkey", "criteria")
        read_only_fields = fields


class MasterSerializer(serializers.ModelSerializer):
    type_licences_acceptees = TypeLicenceSummarySerializer(many=True, read_only=True)
    passerelles_vers = serializers.SlugRelatedField(many=True, read_only=True, slug_field="pubkey")
    passerelles_depuis = serializers.SlugRelatedField(many=True, read_only=True, slug_field="pubkey")
    required_documents = RequiredDocumentSerializer(many=True, read_only=True)
    coordinateur_pubkey = serializers.CharField(source="coordinateur.pubkey", read_only=True)

    class Meta:
        model = Master
        fields = (
            "pubkey", "nom", "universite", "ville", "domaine", "discipline", "specialite",
            "nombre_places", "date_debut", "date_fin", "statut",
            "coordinateur_pubkey", "type_licences_acceptees",
            "passerelles_vers", "passerelles_depuis", "required_documents",
        )
        read_only_fields = fields


class MasterSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Master
        fields = ("pubkey", "nom", "universite", "ville", "domaine", "specialite", "statut")
        read_only_fields = fields