import secrets
from datetime import datetime, timedelta, timezone

from src.apps.authentication.dto.otp_verify import OtpVerifyRequestDTO
from src.shared.exceptions.auth_exceptions import InvalidOtpException

# TODO(infra): remplacer par un modèle Prisma `Otp` persistant (comme dans
# l'autre projet BSM) dès que le schéma est étendu, pour survivre aux
# redémarrages et fonctionner en multi-instance derrière un load balancer.
_OTP_STORE: dict[str, dict] = {}
OTP_TTL_MINUTES = 5
OTP_LENGTH = 6


class OtpService:

    @staticmethod
    def _generate_code() -> str:
        return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))

    @classmethod
    def send_otp(cls, telephone: str) -> None:
        code = cls._generate_code()
        _OTP_STORE[telephone] = {
            "code": code,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES),
            "attempts": 0,
        }

        # TODO(notifications): brancher sur apps/notifications (provider SMS)
        # pour l'envoi réel. En dev, le code peut être loggé :
        # print(f"[DEV OTP] {telephone} -> {code}")

    @staticmethod
    def verify_otp(payload: OtpVerifyRequestDTO) -> bool:
        entry = _OTP_STORE.get(payload.telephone)
        if not entry:
            raise InvalidOtpException()

        if entry["expires_at"] < datetime.now(timezone.utc):
            del _OTP_STORE[payload.telephone]
            raise InvalidOtpException()

        entry["attempts"] += 1
        if entry["attempts"] > 5:
            del _OTP_STORE[payload.telephone]
            raise InvalidOtpException()

        if entry["code"] != payload.code:
            raise InvalidOtpException()

        del _OTP_STORE[payload.telephone]
        return True
