from pydantic import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from src.apps.authentication.services.token_service import TokenService


def validate_dto(dto_class, data):
    try:
        return dto_class.model_validate(data)
    except ValidationError as error:
        raise DRFValidationError(error.errors()) from error


def auth_response(user):
    # RBAC (module `authorization`, via `UserRole`) est l'unique source de
    # vérité pour le rôle. `authentication` ne fait que le lire pour le
    # mettre dans le JWT et la réponse — il ne le stocke ni ne le décide
    # jamais lui-même.
    from src.apps.authorization.services.role_assignment_service import (
        RoleAssignmentService,
    )

    role_code = RoleAssignmentService.get_active_role_code(user)
    tokens = TokenService.create_token_pair(user.pubkey, role_code)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "user": {
            "pubkey": user.pubkey,
            "email": user.email,
            "role": role_code,
            "is_active": user.is_active,
        },
    }
