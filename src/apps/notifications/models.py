from django.db import models


class NotificationMotif(models.TextChoices):
    """Motifs couvrant les deux cas identifiés :
    - documents soumis à la création du profil (pas encore de candidature)
    - documents/rejets liés à une candidature précise
    """

    DOCUMENT_MANQUANT = "DOCUMENT_MANQUANT", "Document manquant"
    DOCUMENT_FRAUDULEUX = "DOCUMENT_FRAUDULEUX", "Document frauduleux"
    DOCUMENT_REJETE = "DOCUMENT_REJETE", "Document rejeté"
    CANDIDATURE_STATUT = "CANDIDATURE_STATUT", "Changement de statut de candidature"
    AUTRE = "AUTRE", "Autre"


class NotificationRecord(models.Model):
    """Table legacy MST_NOTIFICATION_RECORDS, avec le correctif de schéma
    discuté : `candidateProfileId` devient la clé TOUJOURS présente (le
    vrai destinataire), `applicationId` devient optionnel pour couvrir le
    cas où le candidat n'a pas encore postulé (documents de création de
    profil, avant tout clic sur "postuler").

    Voir _PRISMA_SCHEMA_PATCH.prisma à la racine du zip pour le patch
    correspondant à appliquer sur le schema.prisma de référence.
    """

    id = models.AutoField(primary_key=True)
    pubkey = models.TextField(unique=True)

    candidate_profile = models.ForeignKey(
        "candidate_profile.CandidateProfile",
        on_delete=models.CASCADE,
        related_name="notifications",
        db_column="candidateProfileId",
    )

    application = models.ForeignKey(
        "masters.Application",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        db_column="applicationId",
    )

    motif = models.CharField(max_length=32, choices=NotificationMotif.choices)
    document_concerne = models.TextField(null=True, blank=True, db_column="documentConcerne")
    objet = models.TextField()
    corps = models.TextField()

    # Ajout pragmatique hors schéma strict (nécessaire pour une UX "vu/pas
    # vu" côté candidat) — à ajouter au patch Prisma si retenu.
    lu_le = models.DateTimeField(null=True, blank=True, db_column="luLe")

    envoyee_le = models.DateTimeField(auto_now_add=True, db_column="envoyeeLe")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        managed = False
        db_table = "MST_NOTIFICATION_RECORDS"
        indexes = [
            models.Index(fields=["candidate_profile", "lu_le"]),
            models.Index(fields=["application"]),
        ]
