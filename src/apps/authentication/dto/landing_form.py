from pydantic import BaseModel, EmailStr, Field


class LandingFormRequestDTO(BaseModel):
    """
    Formulaire public affiché sur la landing page, rempli AVANT toute
    création de compte : sert à capter un lead (candidat potentiellement
    intéressé par un master précis) sans lui imposer une inscription
    complète. Le service applicatif transforme ensuite ce lead en compte
    réel si le candidat confirme via OTP/email.
    """

    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str = Field(min_length=8, max_length=20)
    master_pubkey: str | None = Field(
        default=None, description="Master ciblé si connu au moment du remplissage"
    )
    message: str | None = Field(default=None, max_length=1000)
