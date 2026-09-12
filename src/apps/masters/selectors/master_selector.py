from src.apps.masters.models import Master, MasterStatus


def get_by_pubkey(pubkey: str) -> Master | None:
    return (
        Master.objects.select_related("coordinateur", "administrateur")
        .prefetch_related(
            "type_licences_acceptees", "passerelles_vers", "passerelles_depuis", "required_documents"
        )
        .filter(pubkey=pubkey, deleted_at__isnull=True)
        .first()
    )


def list_open(domaine: str | None = None):
    qs = Master.objects.filter(statut=MasterStatus.OUVERT, deleted_at__isnull=True)
    if domaine:
        qs = qs.filter(domaine=domaine)
    return qs.order_by("nom")


def list_for_coordinateur(coordinateur_id: int):
    return Master.objects.filter(coordinateur_id=coordinateur_id, deleted_at__isnull=True).order_by("-created_at")


def list_all(statut: str | None = None):
    qs = Master.objects.filter(deleted_at__isnull=True)
    if statut:
        qs = qs.filter(statut=statut)
    return qs.order_by("-created_at")
