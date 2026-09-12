from django.db import models


class ApplicationStatus(models.TextChoices):
    SOUMISE = "SOUMISE", "Soumise"
    EN_COURS = "EN_COURS", "En cours"
    ACCEPTEE = "ACCEPTEE", "Acceptée"
    REJETEE = "REJETEE", "Rejetée"


class Application(models.Model):
    """Table legacy MST_APPLICATIONS. `niveau` distingue une candidature en
    1ère année (parcours classique via `Diplome`) d'une candidature en 2e
    année (passerelle via `Master1Year`, cf. `candidate_profile`)."""

    id = models.AutoField(primary_key=True)
    pubkey = models.TextField(unique=True)

    candidate_profile = models.ForeignKey(
        "candidate_profile.CandidateProfile",
        on_delete=models.CASCADE,
        related_name="applications",
        db_column="candidateProfileId",
    )
    master = models.ForeignKey(
        "masters.Master",
        on_delete=models.PROTECT,
        related_name="applications",
        db_column="masterId",
    )

    niveau = models.TextField()
    date_soumission = models.DateTimeField(auto_now_add=True, db_column="dateSoumission")
    score = models.FloatField(null=True, blank=True)
    statut = models.CharField(
        max_length=16, choices=ApplicationStatus.choices, default=ApplicationStatus.SOUMISE
    )

    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        managed = True
        db_table = "MST_APPLICATIONS"
        constraints = [
            models.UniqueConstraint(
                fields=["candidate_profile", "master"],
                condition=models.Q(deleted_at__isnull=True),
                name="applications_one_active_per_master",
            )
        ]
        indexes = [
            models.Index(fields=["candidate_profile", "statut"]),
            models.Index(fields=["master", "statut"]),
        ]
