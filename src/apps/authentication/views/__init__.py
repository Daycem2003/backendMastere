from pydantic import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from src.apps.authentication.services.token_service import TokenService


def validate_dto(dto_class, data):
    try:
        return dto_class.model_validate(data)
    except ValidationError as error:
        raise DRFValidationError(error.errors()) from error


def auth_response(user):
    tokens = TokenService.create_token_pair(user.pubkey, user.role)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "user": {
            "pubkey": user.pubkey,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }
