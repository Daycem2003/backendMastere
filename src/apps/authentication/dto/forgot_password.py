from pydantic import BaseModel, EmailStr


class ForgotPasswordRequestDTO(BaseModel):
    email: EmailStr
