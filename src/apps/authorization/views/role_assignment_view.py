from fastapi import APIRouter, Depends, status
from asgiref.sync import sync_to_async

from src.apps.authentication.models import UserModel
from src.apps.authorization.dto.role_assignment import (
    RoleAssignmentRequestDTO,
    RoleAssignmentResponseDTO,
)
from src.apps.authorization.dto.role import RoleResponseDTO
from src.apps.authorization.services.role_assignment_service import RoleAssignmentService
from src.apps.authorization.models import UserRole
from src.apps.authorization.serializers.role_assignment_serializer import serialize_role_assignment
from src.apps.authorization.serializers.role_serializer import serialize_role
from src.apps.authorization.permissions.role_based import require_roles
from src.fastapi_app.legacy_auth import get_current_user

router = APIRouter()


@router.post(
    "/user-roles",
    response_model=RoleAssignmentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("ADMIN"))],
)
async def assign_role(
    payload: RoleAssignmentRequestDTO,
    current_user: UserModel = Depends(get_current_user),
) -> RoleAssignmentResponseDTO:
    user_role = await sync_to_async(RoleAssignmentService.assign_role)(
        user_pubkey=payload.user_pubkey,
        role_code=payload.role_code,
        assigned_by_pubkey=current_user.pubkey,
    )
    # Recharge avec la relation `role` pour le serializer.
    user_role = await sync_to_async(
        lambda: UserRole.objects.select_related("role").get(id=user_role.id)
    )()
    return serialize_role_assignment(user_role, payload.user_pubkey)


@router.delete(
    "/user-roles",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("ADMIN"))],
)
async def revoke_role(payload: RoleAssignmentRequestDTO) -> None:
    await sync_to_async(RoleAssignmentService.revoke_role)(payload.user_pubkey, payload.role_code)


@router.get(
    "/user-roles/{user_pubkey}",
    response_model=list[RoleResponseDTO],
    dependencies=[Depends(require_roles("ADMIN"))],
)
async def list_user_roles(user_pubkey: str) -> list[RoleResponseDTO]:
    user_roles = await sync_to_async(RoleAssignmentService.list_user_roles)(user_pubkey)
    return [serialize_role(ur.role) for ur in user_roles]
