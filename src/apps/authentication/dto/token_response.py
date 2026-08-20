from pydantic import BaseModel


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublicDTO(BaseModel):
    pubkey: str
    email: str
    role: str
    is_active: bool


class AuthResponseDTO(BaseModel):
    tokens: TokenResponseDTO
    user: UserPublicDTO
