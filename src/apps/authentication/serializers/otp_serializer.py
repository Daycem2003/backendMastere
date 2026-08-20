from pydantic import BaseModel


class OtpSentResponseDTO(BaseModel):
    message: str = "Un code de vérification a été envoyé."
    expires_in_minutes: int = 5


def serialize_otp_sent() -> OtpSentResponseDTO:
    return OtpSentResponseDTO()
