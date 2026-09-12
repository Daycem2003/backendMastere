from src.apps.authentication.models import UserModel
from src.apps.authentication.dto.token_response import (
    AuthResponseDTO,
    TokenResponseDTO,
    UserPublicDTO,
)


def serialize_authenticated_user(
    user: UserModel, tokens: TokenResponseDTO, role_code: str | None
) -> AuthResponseDTO:
    """`role_code` doit venir de
    `authorization.services.role_assignment_service.RoleAssignmentService.get_active_role_code`
    — jamais de `user.role`, qui n'existe pas sur le modèle `User`
    (RBAC = source unique de vérité, portée par `authorization.UserRole`)."""
    return AuthResponseDTO(
        tokens=tokens,
        user=UserPublicDTO(
            pubkey=user.pubkey,
            email=user.email,
            role=role_code,
            is_active=user.is_active,
        ),
    )
