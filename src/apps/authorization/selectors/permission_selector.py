from asgiref.sync import sync_to_async

from src.apps.authorization.models import Permission


@sync_to_async
def get_permission_by_code(code: str):
    return Permission.objects.filter(code=code).first()


@sync_to_async
def list_permissions():
    return Permission.objects.order_by("resource", "action")
