from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateUserDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="CANDIDATE")
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UpdateUserDTO(BaseModel):
    email: EmailStr | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else None


class ChangePasswordDTO(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_differs(cls, v: str, info) -> str:
        old = info.data.get("old_password")
        if old and v == old:
            raise ValueError("Le nouveau mot de passe doit être différent de l'ancien.")
        return v


class UserFilterDTO(BaseModel):
    search: str | None = None
    is_active: bool | None = None
    is_deleted: bool | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class UserResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pubkey: str
    email: str
    is_active: bool
    is_deleted: bool
    profile_type: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
