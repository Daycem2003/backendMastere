from fastapi import APIRouter, Depends, status

from src.apps.authorization.dto.role import RoleCreateRequestDTO, RoleResponseDTO
from src.apps.authorization.services.role_service import RoleService
from src.apps.authorization.serializers.role_serializer import serialize_role, serialize_roles
from src.apps.authorization.permissions.role_based import require_roles

router = APIRouter(dependencies=[Depends(require_roles("ADMIN"))])


@router.get("/roles", response_model=list[RoleResponseDTO])
async def list_roles() -> list[RoleResponseDTO]:
    roles = await RoleService.list_roles()
    return serialize_roles(roles)


@router.get("/roles/{role_pubkey}", response_model=RoleResponseDTO)
async def get_role(role_pubkey: str) -> RoleResponseDTO:
    role = await RoleService.get_role(role_pubkey)
    return serialize_role(role)


@router.post("/roles", response_model=RoleResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreateRequestDTO) -> RoleResponseDTO:
    role = await RoleService.create_custom_role(payload.code, payload.name, payload.description)
    return serialize_role(role)


@router.delete("/roles/{role_pubkey}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_pubkey: str) -> None:
    await RoleService.delete_role(role_pubkey)


@router.post("/roles/{role_pubkey}/permissions/{permission_code}", response_model=RoleResponseDTO)
async def assign_permission_to_role(role_pubkey: str, permission_code: str) -> RoleResponseDTO:
    role = await RoleService.assign_permission_to_role(role_pubkey, permission_code)
    return serialize_role(role)


@router.delete(
    "/roles/{role_pubkey}/permissions/{permission_code}",
    response_model=RoleResponseDTO,
)
async def revoke_permission_from_role(role_pubkey: str, permission_code: str) -> RoleResponseDTO:
    role = await RoleService.revoke_permission_from_role(role_pubkey, permission_code)
    return serialize_role(role)
