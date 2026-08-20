from django.db import models

from src.shared.models import PostgreSQLEnumField, TimestampedSoftDeleteModel


class CandidateStatus(models.TextChoices):
    PENDING = "EN_ATTENTE", "En attente"
    VALIDATED = "VALIDE", "Validé"
    REJECTED = "REJETE", "Rejeté"


class CandidateProfile(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="candidate_profile", db_column="userId")
    nom = models.TextField()
    prenom = models.TextField()
    cin = models.TextField(unique=True)
    email = models.TextField()
    telephone = models.TextField()
    ville = models.TextField()
    annee_naissance = models.IntegerField(db_column="anneeNaissance")
    statut = PostgreSQLEnumField(enum_name="CandidateStatusEnum", choices=CandidateStatus.choices, default=CandidateStatus.PENDING)

    class Meta:
        managed = False
        db_table = "MST_CANDIDATE_PROFILES"
