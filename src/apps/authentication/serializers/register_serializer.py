from src.apps.authentication.models import UserModel
from src.apps.authentication.dto.token_response import (
    AuthResponseDTO,
    TokenResponseDTO,
    UserPublicDTO,
)


def serialize_new_user(user: UserModel, tokens: TokenResponseDTO) -> AuthResponseDTO:
    return AuthResponseDTO(
        tokens=tokens,
        user=UserPublicDTO(
            pubkey=user.pubkey,
            email=user.email,
            role=user.role,
            is_active=user.isActive,
        ),
    )
