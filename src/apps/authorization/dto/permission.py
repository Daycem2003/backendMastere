from pydantic import BaseModel


class PermissionResponseDTO(BaseModel):
    pubkey: str
    code: str
    resource: str
    action: str
    description: str | None
