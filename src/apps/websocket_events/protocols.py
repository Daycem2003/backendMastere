from typing import Protocol

from src.apps.authentication.interfaces.jwt_payload import JwtPayload


class TokenDecoderProtocol(Protocol):
    """Contrat formel pour le décodage et la validation des jetons JWT."""

    def decode_and_require_type(self, token: str, expected_type: str) -> JwtPayload:
        ...
