from src.apps.authentication.interfaces.jwt_payload import JwtPayload
from src.apps.authentication.services.token_service import TokenService


class JwtRefreshTokenStrategy:
    @staticmethod
    def validate(token: str) -> JwtPayload:
        return TokenService.decode_and_require_type(token, "refresh")
