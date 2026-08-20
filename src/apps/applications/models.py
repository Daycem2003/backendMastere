from django.db import models

from src.shared.models import CreatedSoftDeleteModel, PostgreSQLEnumField, TimestampedSoftDeleteModel


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "SOUMISE", "Soumise"
    IN_REVIEW = "EN_COURS", "En cours"
    ACCEPTED = "ACCEPTEE", "Acceptée"
    REJECTED = "REJETEE", "Rejetée"


class Application(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    candidate_profile = models.ForeignKey("candidate_profile.CandidateProfile", on_delete=models.CASCADE, related_name="applications", db_column="candidateProfileId")
    master = models.ForeignKey("masters.Master", on_delete=models.PROTECT, related_name="applications", db_column="masterId")
    niveau = models.TextField()
    date_soumission = models.DateTimeField(db_column="dateSoumission", db_default=models.functions.Now())
    score = models.FloatField(null=True, blank=True)
    statut = PostgreSQLEnumField(enum_name="ApplicationStatusEnum", choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED)

    class Meta:
        managed = False
        db_table = "MST_APPLICATIONS"


class NotificationRecord(CreatedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="notifications", db_column="applicationId")
    motif = models.TextField()
    document_concerne = models.TextField(null=True, blank=True, db_column="documentConcerne")
    objet = models.TextField()
    corps = models.TextField()
    envoyee_le = models.DateTimeField(db_column="envoyeeLe", db_default=models.functions.Now())

    class Meta:
        managed = False
        db_table = "MST_NOTIFICATION_RECORDS"
