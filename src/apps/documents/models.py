from django.db import models
import uuid
from src.shared.models import CreatedSoftDeleteModel, TimestampedSoftDeleteModel

def generate_slot_pubkey():
    return f"slot_{uuid.uuid4().hex[:24]}"
class DocumentType(models.TextChoices):
    """LEGACY — utilisé uniquement par `Document` (ancien schéma). Plus
    utilisé par le workflow DocumentSlot/DocumentVersion."""
    TRANSCRIPT = "RELEVE_NOTES", "Relevé de notes"
    DIPLOMA = "DIPLOME", "Diplôme"
    EVIDENCE = "JUSTIFICATIF", "Justificatif"
    OTHER = "AUTRE", "Autre"


class Document(CreatedSoftDeleteModel):
    """Table legacy MST_DOCUMENTS. CONSERVÉE TELLE QUELLE pour compatibilité
    avec d'éventuelles anciennes données. N'est PLUS référencée par
    DocumentVersion depuis ce refactor — modèle autonome, hors du nouveau
    workflow."""

    pubkey = models.TextField(unique=True)
    nom = models.TextField()
    type = models.CharField(max_length=32, choices=DocumentType.choices)
    url = models.TextField()
    licence_year = models.OneToOneField("candidate_profile.LicenceYear", on_delete=models.CASCADE, related_name="releve", null=True, blank=True, db_column="licenceYearId")
    diplome = models.OneToOneField("candidate_profile.Diplome", on_delete=models.CASCADE, related_name="pdf", null=True, blank=True, db_column="diplomeId")
    master1_year = models.OneToOneField("candidate_profile.Master1Year", on_delete=models.CASCADE, related_name="releve_m1", null=True, blank=True, db_column="master1YearId")
    redoublement_year = models.ForeignKey("candidate_profile.RedoublementYear", on_delete=models.CASCADE, related_name="justificatifs", null=True, blank=True, db_column="redoublementYearId")

    class Meta:
        managed = True
        db_table = "MST_DOCUMENTS"


class RequiredDocument(TimestampedSoftDeleteModel):
    """`type` doit correspondre à une valeur de SlotType (validé au niveau
    applicatif dans can_candidate_apply, pas par une FK — ce champ reste
    TextField pour ne pas coupler ce modèle au module documents)."""
    pubkey = models.TextField(unique=True)
    master = models.ForeignKey("masters.Master", on_delete=models.CASCADE, related_name="required_documents", db_column="masterId")
    type = models.TextField()

    class Meta:
        managed = True
        db_table = "MST_REQUIRED_DOCUMENTS"


class SlotType(models.TextChoices):
    """Type métier d'une pièce justificative. Remplace tout usage de
    document_type comme clé composite libre : la combinaison
    (type, domaine, annee_licence, redoublement_annee, justificatif_index)
    identifie un DocumentSlot unique pour un candidat."""

    RELEVE_LICENCE = "RELEVE_LICENCE", "Relevé de notes de licence"
    DIPLOME_LICENCE = "DIPLOME_LICENCE", "Diplôme de licence"
    RELEVE_M1 = "RELEVE_M1", "Relevé de notes de M1"
    JUSTIFICATIF_REDOUBLEMENT = "JUSTIFICATIF_REDOUBLEMENT", "Justificatif de redoublement"
    AUTRE = "AUTRE", "Autre"


class AnneeLicence(models.TextChoices):
    NA = "", "Non applicable"
    A1 = "A1", "Année 1"
    A2 = "A2", "Année 2"
    A3 = "A3", "Année 3"


class DocumentSlot(TimestampedSoftDeleteModel):
    """Identité métier UNIQUE d'une pièce justificative pour un candidat.

    Un slot ne contient aucun fichier : c'est un emplacement (ex. "relevé
    de licence Informatique, année A2") qui reçoit plusieurs
    DocumentVersion au fil du temps. C'est la clé d'unicité métier —
    DocumentVersion en dépend, jamais l'inverse.

    IMPORTANT : domaine/annee_licence/redoublement_annee/justificatif_index
    utilisent des défauts NON NULL ("" / 0), jamais NULL. En PostgreSQL,
    NULL != NULL, donc une UniqueConstraint sur des colonnes NULLABLE ne
    bloque rien pour les lignes NULL — c'est exactement le bug qui touchait
    l'ancienne contrainte (document, version_number) avec document
    nullable. Avec "" et 0, la contrainte est réellement appliquée pour
    TOUTES les combinaisons, y compris les slots simples (ex. RELEVE_M1).
    """

    pubkey = models.TextField(
    unique=True,
    default=generate_slot_pubkey,
)
    candidate_profile = models.ForeignKey(
        "candidate_profile.CandidateProfile",
        on_delete=models.CASCADE,
        related_name="document_slots",
        db_column="candidateProfileId",
    )
    type = models.CharField(max_length=32, choices=SlotType.choices)

    domaine = models.TextField(default="", blank=True)
    annee_licence = models.CharField(max_length=2, choices=AnneeLicence.choices, default=AnneeLicence.NA, blank=True)
    redoublement_annee = models.TextField(default="", blank=True)
    justificatif_index = models.PositiveIntegerField(default=0)
    a_redeposer = models.BooleanField(default=False, db_column="aRedeposer")

    class Meta:
        db_table = "DOCUMENT_SLOTS"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "candidate_profile", "type", "domaine",
                    "annee_licence", "redoublement_annee", "justificatif_index",
                ],
                name="documents_slot_unique",
            )
        ]
        indexes = [
            models.Index(fields=["candidate_profile", "type"]),
            models.Index(fields=["pubkey"]),
        ]


class DocumentReviewStatus(models.TextChoices):
    PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class DocumentVersion(models.Model):
    """Un fichier concret uploadé pour un slot donné, à un instant donné.
    L'identité métier du document est le SLOT — plusieurs versions
    successives peuvent exister (rejet -> remplacement -> nouvelle
    version), l'historique complet étant conservé (aucune suppression)."""

    id = models.AutoField(primary_key=True)
    pubkey = models.TextField(unique=True)
    slot = models.ForeignKey(
        DocumentSlot,
        on_delete=models.CASCADE,
        related_name="versions",
        db_column="slotId",
    )
    version_number = models.PositiveIntegerField(db_column="versionNumber")
    status = models.CharField(
        max_length=20,
        choices=DocumentReviewStatus.choices,
        default=DocumentReviewStatus.PENDING_REVIEW,
    )
    storage_key = models.TextField(db_column="storageKey")
    mime_type = models.CharField(max_length=255, db_column="mimeType")
    file_size = models.PositiveBigIntegerField(db_column="fileSize")
    checksum = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True, db_column="isActive")
    reviewer = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_document_versions", db_column="reviewerId",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, db_column="reviewedAt")
    rejection_reason = models.TextField(null=True, blank=True, db_column="rejectionReason")
    replaced_version = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="replacements", db_column="replacedVersionId",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        db_table = "DOCUMENT_VERSIONS"
        constraints = [
            models.UniqueConstraint(fields=["slot", "version_number"], name="documents_version_unique")
        ]
        indexes = [
            models.Index(fields=["slot", "status"]),
            models.Index(fields=["slot", "is_active"]),
            models.Index(fields=["pubkey"]),
        ]


class DocumentAuditEvent(models.Model):
    id = models.AutoField(primary_key=True)
    document_version = models.ForeignKey(
        DocumentVersion, on_delete=models.CASCADE, related_name="audit_events", db_column="documentVersionId",
    )
    action = models.CharField(max_length=32)
    actor = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True,
        related_name="document_audit_events", db_column="actorId",
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")

    class Meta:
        db_table = "DOCUMENT_AUDIT_EVENTS"
        indexes = [models.Index(fields=["document_version", "created_at"])]


class R2OperationCounter(models.Model):
    """Inchangé depuis la migration 0002 — voir usage_budget.py."""
    period = models.CharField(max_length=7, unique=True)
    class_a_count = models.PositiveIntegerField(default=0)
    class_b_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "R2_OPERATION_COUNTERS"