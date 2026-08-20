from src.apps.authentication.interfaces.jwt_payload import JwtPayload
from src.apps.authentication.services.token_service import TokenService


class JwtStrategy:
    @staticmethod
    def validate_access_token(token: str) -> JwtPayload:
        return TokenService.decode_and_require_type(token, "access")
