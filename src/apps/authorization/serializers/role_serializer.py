from src.apps.authorization.dto.role import PermissionSummaryDTO, RoleResponseDTO
from src.apps.authorization.models import Role


def serialize_role(role: Role) -> RoleResponseDTO:
    permissions = [
            PermissionSummaryDTO(
                code=rp.permission.code,
                resource=rp.permission.resource,
                action=rp.permission.action,
            )
            for rp in role.role_permissions.all()
        ]

    return RoleResponseDTO(
        pubkey=role.pubkey,
        code=role.code,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=permissions,
    )


def serialize_roles(roles: list[Role]) -> list[RoleResponseDTO]:
    return [serialize_role(role) for role in roles]
