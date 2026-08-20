import uuid
from datetime import datetime, timedelta, timezone

import bcrypt

from src.apps.users.models import User
from src.shared.exceptions.auth_exceptions import InvalidTokenException

_RESET_TOKENS: dict[str, dict] = {}
RESET_TOKEN_TTL_MINUTES = 30


class PasswordService:
    @staticmethod
    def hash_password(raw_password: str) -> str:
        return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(raw_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode(), hashed_password.encode())
        except (ValueError, TypeError):
            return False

    @staticmethod
    def request_reset(payload) -> None:
        user = User.objects.filter(email=payload.email).only("pubkey").first()
        if user:
            token = uuid.uuid4().hex
            _RESET_TOKENS[token] = {"user_pubkey": user.pubkey, "expires_at": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)}

    @staticmethod
    def reset_password(payload) -> None:
        entry = _RESET_TOKENS.get(payload.token)
        if not entry or entry["expires_at"] < datetime.now(timezone.utc):
            raise InvalidTokenException()
        User.objects.filter(pubkey=entry["user_pubkey"]).update(password=PasswordService.hash_password(payload.new_password))
        del _RESET_TOKENS[payload.token]
