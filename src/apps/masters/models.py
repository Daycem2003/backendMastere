from django.db import models

from src.shared.models import PostgreSQLEnumField, TimestampedSoftDeleteModel


class MasterStatus(models.TextChoices):
    OPEN = "OUVERT", "Ouvert"
    CLOSED = "FERME", "Fermé"
    DRAFT = "BROUILLON", "Brouillon"


class TypeLicence(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    intitule = models.TextField()
    domaine = models.TextField()
    est_eligible = models.BooleanField(default=True, db_column="estEligible")

    class Meta:
        managed = False
        db_table = "MST_TYPE_LICENCES"


class LicenceYear(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    candidate_profile = models.ForeignKey("candidate_profile.CandidateProfile", on_delete=models.CASCADE, related_name="licence_years", db_column="candidateProfileId")
    annee = models.IntegerField()
    annee_universitaire = models.TextField(db_column="anneeUniversitaire")
    moyenne = models.FloatField()

    class Meta:
        managed = False
        db_table = "MST_LICENCE_YEARS"


class Diplome(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    candidate_profile = models.OneToOneField("candidate_profile.CandidateProfile", on_delete=models.CASCADE, related_name="diplome", db_column="candidateProfileId")
    type_licence = models.ForeignKey(TypeLicence, on_delete=models.PROTECT, related_name="diplomes", db_column="typeLicenceId")
    annee_obtention = models.TextField(db_column="anneeObtention")
    universite = models.TextField()

    class Meta:
        managed = False
        db_table = "MST_DIPLOMES"


class Master1Year(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    candidate_profile = models.OneToOneField("candidate_profile.CandidateProfile", on_delete=models.CASCADE, related_name="master1_year", db_column="candidateProfileId")
    annee_universitaire = models.TextField(db_column="anneeUniversitaire")
    moyenne = models.FloatField()
    etablissement = models.TextField()

    class Meta:
        managed = False
        db_table = "MST_MASTER1_YEARS"


class Redoublement(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    candidate_profile = models.OneToOneField("candidate_profile.CandidateProfile", on_delete=models.CASCADE, related_name="redoublement", db_column="candidateProfileId")
    a_redouble = models.BooleanField(default=False, db_column="aRedouble")

    class Meta:
        managed = False
        db_table = "MST_REDOUBLEMENTS"


class RedoublementYear(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    redoublement = models.ForeignKey(Redoublement, on_delete=models.CASCADE, related_name="redoublement_years", db_column="redoublementId")
    annee = models.TextField()

    class Meta:
        managed = False
        db_table = "MST_REDOUBLEMENT_YEARS"


class MasterTypeLicence(models.Model):
    master = models.ForeignKey("Master", on_delete=models.CASCADE, db_column="A")
    type_licence = models.ForeignKey(TypeLicence, on_delete=models.CASCADE, db_column="B")
    pk = models.CompositePrimaryKey("master", "type_licence")

    class Meta:
        managed = False
        db_table = "_MasterTypeLicence"


class MasterPasserelle(models.Model):
    source = models.ForeignKey("Master", on_delete=models.CASCADE, related_name="passerelle_links_from", db_column="A")
    destination = models.ForeignKey("Master", on_delete=models.CASCADE, related_name="passerelle_links_to", db_column="B")
    pk = models.CompositePrimaryKey("source", "destination")

    class Meta:
        managed = False
        db_table = "_MasterPasserelle"


class Master(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    nom = models.TextField()
    universite = models.TextField()
    ville = models.TextField()
    domaine = models.TextField()
    discipline = models.TextField()
    nombre_places = models.IntegerField(db_column="nombrePlaces")
    date_debut = models.DateTimeField(db_column="dateDebut")
    date_fin = models.DateTimeField(db_column="dateFin")
    statut = PostgreSQLEnumField(enum_name="MasterStatusEnum", choices=MasterStatus.choices, default=MasterStatus.DRAFT)
    coordinateur = models.ForeignKey("coordinator.Coordinateur", on_delete=models.PROTECT, related_name="masters", db_column="coordinateurId")
    administrateur = models.ForeignKey("administrator.Administrateur", on_delete=models.PROTECT, related_name="masters", db_column="administrateurId", null=True, blank=True)
    type_licences_acceptees = models.ManyToManyField(TypeLicence, through=MasterTypeLicence, related_name="masters")
    passerelles_vers = models.ManyToManyField("self", through=MasterPasserelle, through_fields=("source", "destination"), symmetrical=False, related_name="passerelles_depuis")

    class Meta:
        managed = False
        db_table = "MST_MASTERS"
