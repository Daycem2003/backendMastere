from asgiref.sync import sync_to_async

from src.apps.authorization.models import Role


@sync_to_async
def get_role_by_pubkey(pubkey: str):
    return Role.objects.prefetch_related("role_permissions__permission").filter(pubkey=pubkey).first()


@sync_to_async
def get_role_by_code(code: str):
    return Role.objects.filter(code=code).first()


@sync_to_async
def list_roles():
    return Role.objects.prefetch_related("role_permissions__permission").order_by("code")
