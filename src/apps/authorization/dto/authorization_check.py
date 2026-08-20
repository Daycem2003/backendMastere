from pydantic import BaseModel


class PermissionCheckRequestDTO(BaseModel):
    permission_code: str


class PermissionCheckResponseDTO(BaseModel):
    permission_code: str
    allowed: bool
