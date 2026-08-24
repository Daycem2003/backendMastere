from src.apps.notifications.models import NotificationRecord


def get_by_pubkey(pubkey: str):
    return (
        NotificationRecord.objects.select_related("candidate_profile", "application")
        .filter(pubkey=pubkey, deleted_at__isnull=True)
        .first()
    )


def list_for_candidate(candidate_profile_pubkey: str, unread_only: bool = False):
    qs = NotificationRecord.objects.filter(
        candidate_profile__pubkey=candidate_profile_pubkey,
        deleted_at__isnull=True,
    )
    if unread_only:
        qs = qs.filter(lu_le__isnull=True)
    return qs.order_by("-envoyee_le")


def unread_count_for_candidate(candidate_profile_pubkey: str) -> int:
    return NotificationRecord.objects.filter(
        candidate_profile__pubkey=candidate_profile_pubkey,
        lu_le__isnull=True,
        deleted_at__isnull=True,
    ).count()
