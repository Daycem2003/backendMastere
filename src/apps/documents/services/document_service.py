import hashlib
import logging
import uuid
from datetime import datetime, timezone

from django.db import transaction

from src.apps.candidate_profile.models import CandidateProfile
from src.apps.documents.constants import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES
from src.apps.documents.dto.document import DocumentUploadDTO
from src.apps.documents.exceptions.document_exceptions import (
    DocumentVersionNotFound,
    FileTooLarge,
    InvalidDocumentTransition,
    RejectionReasonRequired,
    UnsupportedFileType,
)
from src.apps.documents.models import (
    Document,
    DocumentAuditEvent,
    DocumentReviewStatus,
    DocumentVersion,
)
from src.apps.documents.selectors.document_selector import (
    candidate_has_approved_type,
    get_version_by_pubkey,
)
from src.apps.documents.services.storage import StorageBackend

logger = logging.getLogger(__name__)


class DocumentService:
    @staticmethod
    def _version_for_pubkey(pubkey: str) -> DocumentVersion:
        version = get_version_by_pubkey(pubkey)
        if not version:
            raise DocumentVersionNotFound()
        return version

    @staticmethod
    def approve_by_pubkey(pubkey: str, reviewer):
        return DocumentService.approve(DocumentService._version_for_pubkey(pubkey).pk, reviewer)

    @staticmethod
    def reject_by_pubkey(pubkey: str, reviewer, reason: str):
        return DocumentService.reject(DocumentService._version_for_pubkey(pubkey).pk, reviewer, reason)

    @staticmethod
    def get_by_pubkey(pubkey: str) -> DocumentVersion:
        return DocumentService._version_for_pubkey(pubkey)

    @staticmethod
    def store_uploaded_file(uploaded_file, candidate_pubkey: str, storage: StorageBackend) -> dict:
        """FIX: valide et envoie réellement le fichier au storage backend.

        Toutes les métadonnées (taille, mime type, checksum) sont calculées
        ici à partir des octets reçus — jamais acceptées telles quelles
        depuis le client. C'est ce qui manquait dans la version précédente
        (storage.py existait mais n'était jamais appelé).
        """
        if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLarge()

        content_type = uploaded_file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_MIME_TYPES:
            raise UnsupportedFileType()

        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        checksum = hasher.hexdigest()
        uploaded_file.seek(0)

        key = f"{candidate_pubkey}/{uuid.uuid4().hex}_{uploaded_file.name}"
        storage.upload(uploaded_file, key)

        return {
            "storage_key": key,
            "mime_type": content_type,
            "file_size": uploaded_file.size,
            "checksum": checksum,
        }

    @staticmethod
    @transaction.atomic
    def create_version(payload: DocumentUploadDTO, actor) -> DocumentVersion:
        document = (
            Document.objects.filter(pubkey=payload.document_pubkey).first()
            if payload.document_pubkey
            else None
        )
        candidate = CandidateProfile.objects.filter(
            pubkey=payload.candidate_profile_pubkey
        ).first()
        if not candidate:
            raise DocumentVersionNotFound()
        previous = (
            DocumentVersion.objects.select_for_update()
            .filter(
                candidate_profile=candidate,
                document_type=payload.document_type,
                deleted_at__isnull=True,
            )
            .order_by("-version_number")
            .first()
        )
        version_number = (previous.version_number + 1) if previous else 1
        if previous:
            DocumentVersion.objects.filter(pk=previous.pk).update(is_active=False)
        version = DocumentVersion.objects.create(
            pubkey=f"docv_{uuid.uuid4().hex[:24]}",
            document=document,
            candidate_profile=candidate,
            document_type=payload.document_type,
            version_number=version_number,
            storage_key=payload.storage_key,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            checksum=payload.checksum,
            replaced_version=previous,
        )
        DocumentAuditEvent.objects.create(
            document_version=version,
            actor=actor,
            action="UPLOAD" if previous is None else "REPLACEMENT",
        )
        logger.info(
            "document_version_created",
            extra={"document_version_id": version.pk, "actor_id": actor.pk},
        )
        return version

    @staticmethod
    @transaction.atomic
    def approve(version_id: int, reviewer) -> DocumentVersion:
        version = DocumentVersion.objects.select_for_update().get(pk=version_id)
        if version.status != DocumentReviewStatus.PENDING_REVIEW:
            raise InvalidDocumentTransition()
        version.status = DocumentReviewStatus.APPROVED
        version.reviewer = reviewer
        version.reviewed_at = datetime.now(timezone.utc)
        version.rejection_reason = None
        version.save(update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"])
        DocumentAuditEvent.objects.create(
            document_version=version, actor=reviewer, action="APPROVAL"
        )
        return version

    @staticmethod
    @transaction.atomic
    def reject(version_id: int, reviewer, reason: str) -> DocumentVersion:
        if not reason or not reason.strip():
            raise RejectionReasonRequired()
        version = DocumentVersion.objects.select_for_update().get(pk=version_id)
        if version.status != DocumentReviewStatus.PENDING_REVIEW:
            raise InvalidDocumentTransition()
        version.status = DocumentReviewStatus.REJECTED
        version.reviewer = reviewer
        version.reviewed_at = datetime.now(timezone.utc)
        version.rejection_reason = reason.strip()
        version.save(update_fields=["status", "reviewer", "reviewed_at", "rejection_reason"])
        DocumentAuditEvent.objects.create(
            document_version=version,
            actor=reviewer,
            action="REJECTION",
            metadata={"reason": reason.strip()},
        )
        logger.info(
            "document_version_rejected",
            extra={"document_version_id": version.pk, "reviewer_id": reviewer.pk},
        )
        return version

    @staticmethod
    def can_candidate_apply(candidate_profile_id: int, required_types: list[str]) -> bool:
        return all(
            candidate_has_approved_type(candidate_profile_id, document_type)
            for document_type in required_types
        )
