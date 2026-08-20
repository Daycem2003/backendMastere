from django.db.models import Q

from src.apps.documents.models import DocumentReviewStatus, DocumentVersion


def get_version_by_pubkey(pubkey: str):
    return (
        DocumentVersion.objects.select_related(
            "document", "candidate_profile", "reviewer", "replaced_version"
        )
        .prefetch_related("audit_events")
        .filter(document__pubkey=pubkey, deleted_at__isnull=True)
        .order_by("-version_number")
        .first()
    )


def list_candidate_versions(candidate_profile_pubkey: str):
    return DocumentVersion.objects.select_related("document", "reviewer").filter(
        candidate_profile__pubkey=candidate_profile_pubkey,
        deleted_at__isnull=True,
    ).order_by("document_type", "-version_number")


def list_pending_versions():
    return DocumentVersion.objects.select_related(
        "document", "candidate_profile", "reviewer"
    ).filter(
        status=DocumentReviewStatus.PENDING_REVIEW,
        deleted_at__isnull=True,
    ).order_by("created_at")


def candidate_has_approved_type(candidate_profile_id: int, document_type: str) -> bool:
    return DocumentVersion.objects.filter(
        candidate_profile_id=candidate_profile_id,
        document_type=document_type,
        status=DocumentReviewStatus.APPROVED,
        is_active=True,
        deleted_at__isnull=True,
    ).exists()
