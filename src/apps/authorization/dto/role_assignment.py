from pydantic import BaseModel


class RoleAssignmentRequestDTO(BaseModel):
    user_pubkey: str
    role_code: str


class RoleAssignmentResponseDTO(BaseModel):
    user_pubkey: str
    role_code: str
    assigned_at: str
