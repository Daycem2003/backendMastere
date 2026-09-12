from src.apps.documents.models import DocumentReviewStatus, DocumentSlot, DocumentVersion


def get_version_by_pubkey(pubkey: str):
    return (
        DocumentVersion.objects.select_related("slot", "slot__candidate_profile", "reviewer", "replaced_version")
        .prefetch_related("audit_events")
        .filter(pubkey=pubkey, deleted_at__isnull=True)
        .first()
    )


def list_candidate_slots(candidate_profile_pubkey: str):
    return (
        DocumentSlot.objects.filter(candidate_profile__pubkey=candidate_profile_pubkey, deleted_at__isnull=True)
        .prefetch_related("versions")
        .order_by("type", "domaine", "annee_licence")
    )


def list_candidate_versions(candidate_profile_pubkey: str):
    return (
        DocumentVersion.objects.select_related("slot", "reviewer")
        .filter(slot__candidate_profile__pubkey=candidate_profile_pubkey, deleted_at__isnull=True)
        .order_by("slot__type", "-version_number")
    )


def list_pending_versions():
    # FIX (audit initial) : filtre désormais is_active=True — une version
    # remplacée qui restait PENDING_REVIEW n'apparaît plus dans la queue.
    return (
        DocumentVersion.objects.select_related("slot", "slot__candidate_profile", "reviewer")
        .filter(status=DocumentReviewStatus.PENDING_REVIEW, is_active=True, deleted_at__isnull=True)
        .order_by("created_at")
    )


def candidate_has_approved_slots_of_type(candidate_profile_id: int, slot_type: str) -> bool:
    """True si le candidat a AU MOINS UN slot de ce type ET que TOUS ses
    slots de ce type ont une version active APPROVED (aucun manquant,
    pending ou rejeté)."""
    slots = DocumentSlot.objects.filter(
        candidate_profile_id=candidate_profile_id, type=slot_type, deleted_at__isnull=True
    )
    if not slots.exists():
        return False
    for slot in slots:
        active = slot.versions.filter(is_active=True, deleted_at__isnull=True).first()
        if active is None or active.status != DocumentReviewStatus.APPROVED:
            return False
    return True