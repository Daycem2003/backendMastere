import uuid

from asgiref.sync import sync_to_async
from django.db import transaction

from src.apps.authorization.domain.access_rules import DEFAULT_ROLE_PERMISSIONS
from src.apps.authorization.domain.roles import BASE_ROLE_LABELS, BASE_ROLES
from src.apps.authorization.exceptions.authorization_exceptions import CannotModifySystemRoleException, PermissionNotFoundException, RoleAlreadyExistsException, RoleNotFoundException
from src.apps.authorization.models import Permission, Role, RolePermission
from src.apps.authorization.selectors import role_selector


class RoleService:
    @staticmethod
    async def seed_default_roles() -> None:
        await sync_to_async(RoleService._seed_default_roles)()

    @staticmethod
    @transaction.atomic
    def _seed_default_roles() -> None:
        for code in BASE_ROLES:
            role, _ = Role.objects.get_or_create(code=code, defaults={"pubkey": f"role_{uuid.uuid4().hex[:20]}", "name": BASE_ROLE_LABELS[code], "is_system": True})
            permissions = Permission.objects.filter(code__in=DEFAULT_ROLE_PERMISSIONS[code])
            RolePermission.objects.bulk_create([RolePermission(role=role, permission=permission) for permission in permissions], ignore_conflicts=True)

    @staticmethod
    async def list_roles(): return await role_selector.list_roles()

    @staticmethod
    async def get_role(pubkey: str):
        role = await role_selector.get_role_by_pubkey(pubkey)
        if not role: raise RoleNotFoundException()
        return role

    @staticmethod
    async def create_custom_role(code: str, name: str, description: str | None):
        if await role_selector.get_role_by_code(code): raise RoleAlreadyExistsException()
        try:
            return await sync_to_async(Role.objects.create)(
                pubkey=f"role_{uuid.uuid4().hex[:20]}",
                code=code,
                name=name,
                description=description,
            )
        except IntegrityError as error:
            raise RoleAlreadyExistsException() from error

    @staticmethod
    async def update_role(pubkey: str, name: str, description: str | None):
        role = await RoleService.get_role(pubkey)
        if role.is_system:
            raise CannotModifySystemRoleException()
        role.name = name
        role.description = description
        await sync_to_async(role.save)(update_fields=["name", "description"])
        return await RoleService.get_role(pubkey)

    @staticmethod
    async def delete_role(pubkey: str) -> None:
        role = await RoleService.get_role(pubkey)
        if role.is_system or getattr(role, "isSystem", False): raise CannotModifySystemRoleException()
        await sync_to_async(role.delete)()

    @staticmethod
    async def assign_permission_to_role(role_pubkey: str, permission_code: str):
        role = await RoleService.get_role(role_pubkey)
        permission = await sync_to_async(Permission.objects.filter(code=permission_code).first)()
        if not permission: raise PermissionNotFoundException()
        await sync_to_async(RolePermission.objects.get_or_create)(role=role, permission=permission)
        return await RoleService.get_role(role_pubkey)

    @staticmethod
    async def revoke_permission_from_role(role_pubkey: str, permission_code: str):
        role = await RoleService.get_role(role_pubkey)
        await sync_to_async(RolePermission.objects.filter(role=role, permission__code=permission_code).delete)()
        return await RoleService.get_role(role_pubkey)
