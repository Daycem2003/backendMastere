from dataclasses import Field

from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


import uuid


class CandidateStatus(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    VALIDE = "VALIDE", "Validé"
    REJETE = "REJETE", "Rejeté"


class CandidateProfile(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    user = models.OneToOneField(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="candidate_profile",
        db_column="userId",
        null=True,
        blank=True,
    )

    onboarding_token = models.TextField(
        unique=True,
        null=True,
        blank=True,
    )

    nom = models.TextField()
    nationalite = models.CharField(max_length=100, default="")
    prenom = models.TextField()
    cin = models.TextField(unique=True)
    email = models.TextField()
    telephone = models.TextField()
    ville = models.TextField()
    annee_naissance = models.IntegerField(db_column="anneeNaissance")
    statut = models.CharField(
        max_length=16,
        choices=CandidateStatus.choices,
        default=CandidateStatus.EN_ATTENTE,
    )

    class Meta:
        managed = True
        db_table = "MST_CANDIDATE_PROFILES"

class TypeLicence(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    intitule = models.TextField()
    domaine = models.TextField()
    est_eligible = models.BooleanField(default=True, db_column="estEligible")

    class Meta:
        managed = True
        db_table = "MST_TYPE_LICENCES"


class LicenceYear(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    candidate_profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="licence_years",
        db_column="candidateProfileId",
    )

    type_licence = models.ForeignKey(
        TypeLicence,
        on_delete=models.PROTECT,
        related_name="licence_years",
        db_column="typeLicenceId",
    )

    annee = models.IntegerField()
    annee_universitaire = models.TextField(db_column="anneeUniversitaire")
    moyenne = models.FloatField()

    class Meta:
        managed = True
        db_table = "MST_LICENCE_YEARS"


class Diplome(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    candidate_profile = models.ForeignKey(
    CandidateProfile,
    on_delete=models.CASCADE,
    related_name="diplomes",
    db_column="candidateProfileId",
)
    type_licence = models.ForeignKey(
        TypeLicence,
        on_delete=models.PROTECT,
        related_name="diplomes",
        db_column="typeLicenceId",
    )

    annee_obtention = models.TextField(db_column="anneeObtention")
    universite = models.TextField()

    class Meta:
        managed = True
        db_table = "MST_DIPLOMES"


class Master1Year(TimestampedSoftDeleteModel):
    """NOTE (passerelle M1 -> M2) : `master` est un ajout par rapport au
    schéma Prisma d'origine, où `etablissement` était une simple chaîne de
    texte sans lien formel avec un `Master` de la plateforme — rendant le
    graphe `Master.passerellesVers/Depuis` inexploitable automatiquement.

    `master` reste NULLABLE : un M1 fait hors plateforme reste possible et
    continue d'être décrit par `etablissement` en texte libre. Quand le M1
    a été fait sur un `Master` existant, le renseigner permet à
    `eligibility_service` de vérifier automatiquement l'éligibilité en
    passerelle plutôt que de comparer des chaînes de texte.

    Voir _PRISMA_SCHEMA_PATCH.prisma à la racine du zip.
    """

    pubkey = models.TextField(unique=True)

    candidate_profile = models.OneToOneField(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="master1_year",
        db_column="candidateProfileId",
    )
    master = models.ForeignKey(
        "masters.Master",
        on_delete=models.SET_NULL,
        related_name="m1_origin_years",
        null=True,
        blank=True,
        db_column="masterId",
    )

    annee_universitaire = models.TextField(db_column="anneeUniversitaire")
    moyenne = models.FloatField()
    etablissement = models.TextField()

    class Meta:
        managed = True
        db_table = "MST_MASTER1_YEARS"


class Redoublement(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    candidate_profile = models.OneToOneField(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="redoublement",
        db_column="candidateProfileId",
    )
    a_redouble = models.BooleanField(default=False, db_column="aRedouble")

    class Meta:
        managed = True
        db_table = "MST_REDOUBLEMENTS"


class RedoublementYear(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    redoublement = models.ForeignKey(
        Redoublement,
        on_delete=models.CASCADE,
        related_name="redoublement_years",
        db_column="redoublementId",
    )
    annee = models.TextField()

    class Meta:
        managed = True
        db_table = "MST_REDOUBLEMENT_YEARS"
