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
        "applications.Application",
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

    piece_jointe_cle = models.TextField(null=True, blank=True, db_column="pieceJointeCle")
    piece_jointe_nom = models.TextField(null=True, blank=True, db_column="pieceJointeNom")

    lu_le = models.DateTimeField(null=True, blank=True, db_column="luLe")

    envoyee_le = models.DateTimeField(auto_now_add=True, db_column="envoyeeLe")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        managed = True
        db_table = "MST_NOTIFICATION_RECORDS"
        indexes = [
            models.Index(fields=["candidate_profile", "lu_le"]),
            models.Index(fields=["application"]),
        ]


class BroadcastTarget(models.TextChoices):
    COORDINATEURS = "COORDINATEURS", "Coordinateurs"
    CANDIDATS = "CANDIDATS", "Candidats"
    TOUS = "TOUS", "Tous"
    MASTER_RANG = "MASTER_RANG", "Par rang de Master"


class BroadcastNotification(models.Model):
    id = models.AutoField(primary_key=True)
    pubkey = models.TextField(unique=True)
    cible = models.CharField(
        max_length=32,
        choices=BroadcastTarget.choices,
        default=BroadcastTarget.TOUS,
        db_column="cible",
    )
    master = models.ForeignKey(
        "masters.Master",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="broadcast_notifications",
        db_column="masterId",
    )
    rang_max = models.IntegerField(null=True, blank=True, db_column="rangMax")
    objet = models.TextField()
    message = models.TextField()
    piece_jointe_cle = models.TextField(null=True, blank=True, db_column="pieceJointeCle")
    piece_jointe_nom = models.TextField(null=True, blank=True, db_column="pieceJointeNom")
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="broadcast_notifications",
        db_column="createdById",
    )
    envoyee_le = models.DateTimeField(auto_now_add=True, db_column="envoyeeLe")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")

    class Meta:
        managed = True
        db_table = "MST_BROADCAST_NOTIFICATIONS"
        ordering = ["-envoyee_le"]

