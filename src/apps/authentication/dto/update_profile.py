from pydantic import BaseModel, Field


class UpdateProfileRequestDTO(BaseModel):
    """
    Tous les champs sont optionnels : seuls les champs fournis sont mis à
    jour (patch partiel). La validation "non vide si fourni" est faite via
    les contraintes min_length.
    """

    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    telephone: str | None = Field(default=None, min_length=8, max_length=20)
    ville: str | None = Field(default=None, min_length=1)
