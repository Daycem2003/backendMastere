from src.apps.authorization.models import UserRole
from src.apps.authorization.dto.role_assignment import RoleAssignmentResponseDTO


def serialize_role_assignment(user_role: UserRole, user_pubkey: str) -> RoleAssignmentResponseDTO:
    return RoleAssignmentResponseDTO(
        user_pubkey=user_pubkey,
        role_code=user_role.role.code,
        assigned_at=user_role.assigned_at.isoformat() if user_role.assigned_at else "",
    )
