from django.db import models

from src.shared.models import CreatedSoftDeleteModel, PostgreSQLEnumField, TimestampedSoftDeleteModel


class DocumentType(models.TextChoices):
    TRANSCRIPT = "RELEVE_NOTES", "Relevé de notes"
    DIPLOMA = "DIPLOME", "Diplôme"
    EVIDENCE = "JUSTIFICATIF", "Justificatif"
    OTHER = "AUTRE", "Autre"


class Document(CreatedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    nom = models.TextField()
    type = PostgreSQLEnumField(enum_name="DocumentTypeEnum", choices=DocumentType.choices)
    url = models.TextField()
    licence_year = models.OneToOneField("masters.LicenceYear", on_delete=models.CASCADE, related_name="releve", null=True, blank=True, db_column="licenceYearId")
    diplome = models.OneToOneField("masters.Diplome", on_delete=models.CASCADE, related_name="pdf", null=True, blank=True, db_column="diplomeId")
    master1_year = models.OneToOneField("masters.Master1Year", on_delete=models.CASCADE, related_name="releve_m1", null=True, blank=True, db_column="master1YearId")
    redoublement_year = models.ForeignKey("masters.RedoublementYear", on_delete=models.CASCADE, related_name="justificatifs", null=True, blank=True, db_column="redoublementYearId")

    class Meta:
        managed = False
        db_table = "MST_DOCUMENTS"


class RequiredDocument(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    master = models.ForeignKey("masters.Master", on_delete=models.CASCADE, related_name="required_documents", db_column="masterId")
    type = models.TextField()

    class Meta:
        managed = False
        db_table = "MST_REQUIRED_DOCUMENTS"


class DocumentReviewStatus(models.TextChoices):
    PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class DocumentVersion(models.Model):
    """Workflow metadata for a legacy document without altering MST_DOCUMENTS."""

    id = models.AutoField(primary_key=True)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="versions",
        db_column="documentId",
    )
    candidate_profile = models.ForeignKey(
        "candidate_profile.CandidateProfile",
        on_delete=models.CASCADE,
        related_name="document_versions",
        db_column="candidateProfileId",
    )
    version_number = models.PositiveIntegerField(db_column="versionNumber")
    document_type = models.CharField(max_length=32, db_column="documentType")
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
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_document_versions",
        db_column="reviewerId",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, db_column="reviewedAt")
    rejection_reason = models.TextField(
        null=True, blank=True, db_column="rejectionReason"
    )
    replaced_version = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replacements",
        db_column="replacedVersionId",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        db_table = "DOCUMENT_VERSIONS"
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="documents_document_version_unique",
            )
        ]
        indexes = [
            models.Index(fields=["candidate_profile", "status"]),
            models.Index(fields=["candidate_profile", "is_active"]),
        ]


class DocumentAuditEvent(models.Model):
    id = models.AutoField(primary_key=True)
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.CASCADE,
        related_name="audit_events",
        db_column="documentVersionId",
    )
    action = models.CharField(max_length=32)
    actor = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="document_audit_events",
        db_column="actorId",
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")

    class Meta:
        db_table = "DOCUMENT_AUDIT_EVENTS"
        indexes = [models.Index(fields=["document_version", "created_at"])]
