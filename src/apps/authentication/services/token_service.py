from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from src.config.settings.development import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.apps.authentication.dto.token_response import TokenResponseDTO
from src.apps.authentication.interfaces.jwt_payload import JwtPayload
from src.shared.exceptions.auth_exceptions import InvalidTokenException


class TokenService:
    """
    Point d'entrée unique pour tout ce qui touche aux JWT. Aucune autre
    couche du module ne doit appeler `jose.jwt` directement — ça garde la
    politique d'expiration et l'algorithme centralisés en un seul endroit.
    """

    @staticmethod
    def _encode(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload: JwtPayload = {
            "sub": subject,
            "role": role,
            "type": token_type,  # type: ignore[typeddict-item]
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @classmethod
    def create_access_token(cls, subject: str, role: str) -> str:
        return cls._encode(
            subject, role, "access", timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    @classmethod
    def create_refresh_token(cls, subject: str, role: str) -> str:
        return cls._encode(
            subject, role, "refresh", timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )

    @classmethod
    def create_token_pair(cls, subject: str, role: str) -> TokenResponseDTO:
        return TokenResponseDTO(
            access_token=cls.create_access_token(subject, role),
            refresh_token=cls.create_refresh_token(subject, role),
        )

    @staticmethod
    def decode(token: str) -> JwtPayload:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload  # type: ignore[return-value]
        except JWTError:
            raise InvalidTokenException()

    @classmethod
    def decode_and_require_type(cls, token: str, expected_type: str) -> JwtPayload:
        payload = cls.decode(token)
        if payload.get("type") != expected_type:
            raise InvalidTokenException()
        return payload

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> TokenResponseDTO:
        payload = cls.decode_and_require_type(refresh_token, "refresh")
        return cls.create_token_pair(subject=payload["sub"], role=payload["role"])
