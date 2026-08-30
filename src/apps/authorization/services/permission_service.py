import uuid

from asgiref.sync import sync_to_async

from src.apps.authorization.domain.permissions import PERMISSION_CATALOG
from src.apps.authorization.exceptions.authorization_exceptions import (
    PermissionNotFoundException,
)
from src.apps.authorization.models import Permission
from src.apps.authorization.selectors import permission_selector


class PermissionService:
    @staticmethod
    async def seed_default_permissions() -> None:
        await sync_to_async(PermissionService._seed_default_permissions)()

    @staticmethod
    def _seed_default_permissions() -> None:
        for definition in PERMISSION_CATALOG:
            Permission.objects.get_or_create(code=definition.code, defaults={"pubkey": f"perm_{uuid.uuid4().hex[:20]}", "resource": definition.resource, "action": definition.action, "description": definition.description})

    @staticmethod
    async def list_permissions():
        return await permission_selector.list_permissions()

    @staticmethod
    async def get_permission(code: str):
        permission = await permission_selector.get_permission_by_code(code)
        if not permission:
            raise PermissionNotFoundException()
        return permission
