from src.apps.authorization.models import Permission
from src.apps.authorization.dto.permission import PermissionResponseDTO


def serialize_permission(permission: Permission) -> PermissionResponseDTO:
    return PermissionResponseDTO(
        pubkey=permission.pubkey,
        code=permission.code,
        resource=permission.resource,
        action=permission.action,
        description=permission.description,
    )


def serialize_permissions(permissions: list[Permission]) -> list[PermissionResponseDTO]:
    return [serialize_permission(p) for p in permissions]
