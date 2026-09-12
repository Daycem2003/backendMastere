from pydantic import BaseModel


class SetActiveStatusDTO(BaseModel):
    is_active: bool
    reason: str | None = None


class CreateUserIdentityDTO(BaseModel):
    """Identité pure — aucun rôle. `password_hash` est déjà haché : le
    hachage lui-même reste la responsabilité de `authentication`
    (`PasswordService`), `users` ne fait aucune cryptographie."""

    email: str
    password_hash: str
