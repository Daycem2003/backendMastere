from pydantic import BaseModel


class PasswordActionResponseDTO(BaseModel):
    message: str


def serialize_forgot_password_sent() -> PasswordActionResponseDTO:
    return PasswordActionResponseDTO(
        message="Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."
    )


def serialize_password_reset_success() -> PasswordActionResponseDTO:
    return PasswordActionResponseDTO(message="Mot de passe réinitialisé avec succès.")
