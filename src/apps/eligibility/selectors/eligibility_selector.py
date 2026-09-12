from src.apps.eligibility.models import EligibilityCriteria


def get_by_pubkey(pubkey: str) -> EligibilityCriteria | None:
    return EligibilityCriteria.objects.select_related("master").filter(
        pubkey=pubkey, deleted_at__isnull=True
    ).first()


def list_for_master(master_pubkey: str):
    return EligibilityCriteria.objects.filter(
        master__pubkey=master_pubkey, deleted_at__isnull=True
    ).order_by("criterion")
