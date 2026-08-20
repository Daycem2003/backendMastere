from pydantic import BaseModel, Field, field_validator


class ResetPasswordRequestDTO(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        if not any(char.isdigit() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        if not any(char.isalpha() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins une lettre.")
        return value
