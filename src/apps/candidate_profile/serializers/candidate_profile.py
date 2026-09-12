from rest_framework import serializers

from src.apps.candidate_profile.models import (
    CandidateProfile,
    Diplome,
    LicenceYear,
    Master1Year,
    Redoublement,
    RedoublementYear,
    TypeLicence,
)


class CreateCandidateProfileSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    cin = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    telephone = serializers.CharField(max_length=20)
    ville = serializers.CharField(max_length=100)
    nationalite = serializers.CharField(max_length=100)
    annee_naissance = serializers.IntegerField()


class UpdateCandidateProfileSerializer(serializers.Serializer):
    telephone = serializers.CharField(max_length=20, required=False)
    ville = serializers.CharField(max_length=100, required=False)
    nationalite = serializers.CharField(max_length=100)


class TypeLicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeLicence
        fields = ("pubkey", "intitule", "domaine", "est_eligible")
        read_only_fields = fields


class LicenceYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenceYear
        fields = ("pubkey", "annee", "annee_universitaire", "moyenne")
        read_only_fields = fields


class CreateLicenceYearSerializer(serializers.Serializer):
    type_licence_pubkey = serializers.CharField()
    annee = serializers.IntegerField()
    annee_universitaire = serializers.CharField(max_length=20)
    moyenne = serializers.FloatField(min_value=0, max_value=20)


class DiplomeSerializer(serializers.ModelSerializer):
    type_licence = TypeLicenceSerializer(read_only=True)

    class Meta:
        model = Diplome
        fields = ("pubkey", "type_licence", "annee_obtention", "universite")
        read_only_fields = fields


class CreateDiplomeSerializer(serializers.Serializer):
    type_licence_pubkey = serializers.CharField()
    annee_obtention = serializers.CharField(max_length=10)
    universite = serializers.CharField(max_length=200)


class Master1YearSerializer(serializers.ModelSerializer):
    master_pubkey = serializers.CharField(source="master.pubkey", default=None, read_only=True)

    class Meta:
        model = Master1Year
        fields = ("pubkey", "annee_universitaire", "moyenne", "etablissement", "master_pubkey")
        read_only_fields = fields


class CreateMaster1YearSerializer(serializers.Serializer):
    annee_universitaire = serializers.CharField(max_length=20)
    moyenne = serializers.FloatField(min_value=0, max_value=20)
    etablissement = serializers.CharField(max_length=200)
    master_pubkey = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class RedoublementYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedoublementYear
        fields = ("pubkey", "annee")
        read_only_fields = fields


class RedoublementSerializer(serializers.ModelSerializer):
    redoublement_years = RedoublementYearSerializer(many=True, read_only=True)

    class Meta:
        model = Redoublement
        fields = ("pubkey", "a_redouble", "redoublement_years")
        read_only_fields = fields

class SetRedoublementSerializer(serializers.Serializer):
    a_redouble = serializers.BooleanField()
    annees = serializers.ListField(child=serializers.CharField(max_length=20), required=False)


class CandidateProfileSerializer(serializers.ModelSerializer):
    diplomes = DiplomeSerializer(many=True, read_only=True)
    master1_year = Master1YearSerializer(read_only=True)
    redoublement = RedoublementSerializer(read_only=True)
    licence_years = LicenceYearSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = (
            "pubkey", "nom", "prenom", "cin", "email", "telephone", "ville",
            "annee_naissance", "statut", "diplomes", "master1_year",
            "redoublement", "licence_years", "nationalite"
        )
        read_only_fields = fields
