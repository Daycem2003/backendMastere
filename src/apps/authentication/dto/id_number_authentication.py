from pydantic import BaseModel, Field


class IdNumberAuthRequestDTO(BaseModel):
    """
    Authentification alternative par CIN, utile lorsque le candidat ne se
    souvient plus de l'email utilisé à l'inscription. Le téléphone sert de
    facteur de vérification secondaire (pas de mot de passe dans ce flux ;
    il débouche sur l'envoi d'un OTP par SMS, voir otp_service.py).
    """

    cin: str = Field(min_length=8, max_length=20)
    telephone: str = Field(min_length=8, max_length=20)
