from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    cin: str = Field(min_length=8, max_length=20)
    telephone: str = Field(min_length=8, max_length=20)
    ville: str
    annee_naissance: int = Field(ge=1930, le=2015)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        if not any(char.isdigit() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        if not any(char.isalpha() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins une lettre.")
        return value
