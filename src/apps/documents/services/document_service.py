import hashlib
import logging
import re
import unicodedata
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
    InvalidSlotType,
    RejectionReasonRequired,
    UnsupportedFileType,
)
from src.apps.documents.models import (
    DocumentAuditEvent,
    DocumentReviewStatus,
    DocumentSlot,
    DocumentVersion,
    SlotType,
)
from src.apps.documents.selectors.document_selector import (
    candidate_has_approved_slots_of_type,
    get_version_by_pubkey,
)
from src.apps.documents.services.usage_budget import assert_upload_allowed
from src.apps.documents.services.storage import StorageBackend

logger = logging.getLogger(__name__)


def normalize_name_segment(s: str) -> str:
    """Normalise un segment (nom, prénom, CIN) pour une clé R2 / S3 :
    1. Retrait des accents (NFD).
    2. Suppression de tout caractère hors [a-zA-Z0-9_-].
    3. Préservation de la casse d'origine des caractères.
    """
    if not s:
        return ""
    normalized = unicodedata.normalize("NFD", str(s))
    without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9_-]", "", without_accents.strip())


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
    def store_uploaded_file(uploaded_file, candidate_profile, storage: StorageBackend) -> dict:
        if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLarge()

        content_type = uploaded_file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_MIME_TYPES:
            raise UnsupportedFileType()

        # Budget R2 interne — voir usage_budget.py. Lève StorageQuotaExceeded
        # AVANT tout calcul coûteux (hash) ou appel réel au storage.
        assert_upload_allowed(uploaded_file.size)

        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        checksum = hasher.hexdigest()
        uploaded_file.seek(0)

        # Construction de la clé R2 : {nom}_{prenom}_{cin}/{nom_fichier}
        nom = getattr(candidate_profile, "nom", "")
        prenom = getattr(candidate_profile, "prenom", "")
        cin = getattr(candidate_profile, "cin", "")

        if nom or prenom or cin:
            folder_prefix = f"{normalize_name_segment(nom)}_{normalize_name_segment(prenom)}_{normalize_name_segment(cin)}"
        else:
            folder_prefix = normalize_name_segment(str(candidate_profile))

        key = f"{folder_prefix}/{uploaded_file.name}"
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
        if payload.slot.slot_type not in SlotType.values:
            raise InvalidSlotType()

        # FIX (audit initial, race condition) : on verrouille TOUJOURS une
        # ligne existante (le candidat), jamais un queryset potentiellement
        # vide comme l'ancien select_for_update() sur `previous` — ça
        # sérialise correctement les créations concurrentes, y compris le
        # tout premier upload.
        candidate = (
            CandidateProfile.objects.select_for_update()
            .filter(pubkey=payload.candidate_profile_pubkey)
            .first()
        )
        if not candidate:
            raise DocumentVersionNotFound()

        slot, _ = DocumentSlot.objects.get_or_create(
            candidate_profile=candidate,
            type=payload.slot.slot_type,
            domaine=payload.slot.domaine,
            annee_licence=payload.slot.annee_licence,
            redoublement_annee=payload.slot.redoublement_annee,
            justificatif_index=payload.slot.justificatif_index,
            defaults={"pubkey": f"slot_{uuid.uuid4().hex[:24]}"},
        )
        if getattr(slot, "a_redeposer", False):
            slot.a_redeposer = False
            slot.save(update_fields=["a_redeposer", "updated_at"])

        previous = (
            DocumentVersion.objects.select_for_update()
            .filter(slot=slot, deleted_at__isnull=True)
            .order_by("-version_number")
            .first()
        )
        version_number = (previous.version_number + 1) if previous else 1
        if previous:
            DocumentVersion.objects.filter(pk=previous.pk).update(is_active=False)

        version = DocumentVersion.objects.create(
            pubkey=f"docv_{uuid.uuid4().hex[:24]}",
            slot=slot,
            version_number=version_number,
            storage_key=payload.storage_key,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            checksum=payload.checksum,
            replaced_version=previous,
        )
        authenticated_actor = actor if (actor and getattr(actor, "is_authenticated", False)) else None
        DocumentAuditEvent.objects.create(
            document_version=version,
            actor=authenticated_actor,
            action="UPLOAD" if previous is None else "REPLACEMENT",
        )
        logger.info(
            "document_version_created",
            extra={
                "document_version_id": version.pk,
                "slot_id": slot.pk,
                "actor_id": getattr(authenticated_actor, "pk", None),
            },
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
        DocumentAuditEvent.objects.create(document_version=version, actor=reviewer, action="APPROVAL")
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
            document_version=version, actor=reviewer, action="REJECTION", metadata={"reason": reason.strip()},
        )
        logger.info("document_version_rejected", extra={"document_version_id": version.pk, "reviewer_id": reviewer.pk})
        return version

    @staticmethod
    def can_candidate_apply(candidate_profile_id: int, required_slot_types: list[str]) -> bool:
        return all(
            candidate_has_approved_slots_of_type(candidate_profile_id, slot_type)
            for slot_type in required_slot_types
        )