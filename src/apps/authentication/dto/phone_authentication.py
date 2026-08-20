from pydantic import BaseModel, Field


class PhoneAuthRequestDTO(BaseModel):
    """
    Première étape d'une connexion par téléphone : le candidat fournit son
    numéro, reçoit un OTP par SMS (otp_service.py), puis confirme via
    otp_verify.py pour obtenir ses tokens.
    """

    telephone: str = Field(min_length=8, max_length=20)
