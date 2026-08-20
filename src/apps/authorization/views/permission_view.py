from fastapi import APIRouter, Depends

from src.apps.authorization.dto.permission import PermissionResponseDTO
from src.apps.authorization.services.permission_service import PermissionService
from src.apps.authorization.serializers.permission_serializer import serialize_permissions
from src.apps.authorization.permissions.role_based import require_roles

router = APIRouter(dependencies=[Depends(require_roles("ADMIN"))])


@router.get("/permissions", response_model=list[PermissionResponseDTO])
async def list_permissions() -> list[PermissionResponseDTO]:
    permissions = await PermissionService.list_permissions()
    return serialize_permissions(permissions)
