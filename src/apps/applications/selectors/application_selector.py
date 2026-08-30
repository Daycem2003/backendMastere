from src.apps.applications.models import Application


def get_by_pubkey(pubkey: str) -> Application | None:
    return (
        Application.objects.select_related(
            "candidate_profile", "master", "master__coordinateur"
        )
        .filter(pubkey=pubkey, deleted_at__isnull=True)
        .first()
    )


def get_active_for_candidate_and_master(candidate_profile_id: int, master_id: int) -> Application | None:
    return Application.objects.filter(
        candidate_profile_id=candidate_profile_id,
        master_id=master_id,
        deleted_at__isnull=True,
    ).first()


def list_for_candidate(candidate_profile_pubkey: str):
    return (
        Application.objects.select_related("master")
        .filter(candidate_profile__pubkey=candidate_profile_pubkey, deleted_at__isnull=True)
        .order_by("-date_soumission")
    )


def list_for_master(master_pubkey: str, statut: str | None = None):
    qs = Application.objects.select_related("candidate_profile").filter(
        master__pubkey=master_pubkey, deleted_at__isnull=True
    )
    if statut:
        qs = qs.filter(statut=statut)
    return qs.order_by("-score", "date_soumission")
