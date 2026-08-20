from pydantic import BaseModel, Field


class OtpVerifyRequestDTO(BaseModel):
    telephone: str = Field(min_length=8, max_length=20)
    code: str = Field(min_length=4, max_length=8)
