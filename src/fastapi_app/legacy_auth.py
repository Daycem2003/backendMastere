from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.apps.authentication.models import UserModel
from src.apps.authentication.strategies.jwt_strategy import JwtStrategy
from src.shared.exceptions.auth_exceptions import InactiveUserException, InvalidTokenException

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserModel:
    payload = JwtStrategy.validate_access_token(credentials.credentials)
    user = UserModel.objects.filter(pubkey=payload["sub"]).first()
    if not user:
        raise InvalidTokenException()
    if not user.is_active:
        raise InactiveUserException()
    return user
