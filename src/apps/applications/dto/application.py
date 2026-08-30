from pydantic import BaseModel, Field


class SubmitApplicationDTO(BaseModel):
    master_pubkey: str


class DecisionDTO(BaseModel):
    accept: bool
    motif: str | None = Field(default=None, max_length=2000)
