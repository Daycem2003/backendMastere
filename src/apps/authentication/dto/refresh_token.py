from pydantic import BaseModel


class RefreshTokenRequestDTO(BaseModel):
    refresh_token: str
