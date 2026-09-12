from django.db.models import Q
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
    qs = Application.objects.select_related("candidate_profile", "master").filter(
        master__pubkey=master_pubkey, deleted_at__isnull=True
    )
    if statut and statut.strip() and statut.upper() != "TOUS":
        qs = qs.filter(statut=statut.strip().upper())
    return qs.order_by("-score", "date_soumission")


def list_all(statut: str | None = None, master_pubkey: str | None = None, q: str | None = None):
    qs = Application.objects.select_related("candidate_profile", "master").filter(
        deleted_at__isnull=True
    )
    if master_pubkey and master_pubkey.strip() and master_pubkey.upper() != "TOUS":
        qs = qs.filter(master__pubkey=master_pubkey.strip())
    if statut and statut.strip() and statut.upper() != "TOUS":
        qs = qs.filter(statut=statut.strip().upper())
    if q and q.strip():
        search = q.strip()
        qs = qs.filter(
            Q(candidate_profile__nom__icontains=search)
            | Q(candidate_profile__prenom__icontains=search)
            | Q(candidate_profile__cin__icontains=search)
            | Q(candidate_profile__email__icontains=search)
            | Q(master__nom__icontains=search)
        )
    return qs.order_by("-score", "date_soumission")

