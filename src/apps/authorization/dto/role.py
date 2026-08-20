from pydantic import BaseModel, Field


class RoleCreateRequestDTO(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z_]+$")
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class PermissionSummaryDTO(BaseModel):
    code: str
    resource: str
    action: str


class RoleResponseDTO(BaseModel):
    pubkey: str
    code: str
    name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionSummaryDTO] = []
