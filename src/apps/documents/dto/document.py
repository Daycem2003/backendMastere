from pydantic import BaseModel, Field


class DocumentUploadDTO(BaseModel):
    """DTO interne construit par la vue à partir du fichier réellement reçu
    et des valeurs calculées côté serveur (taille, mime type, checksum) —
    jamais depuis des champs déclarés tels quels par le client."""

    document_pubkey: str | None = None
    candidate_profile_pubkey: str
    document_type: str = Field(min_length=2, max_length=32)
    storage_key: str = Field(min_length=1)
    mime_type: str = Field(min_length=1, max_length=255)
    file_size: int = Field(ge=0)
    checksum: str = ""


class DocumentRejectionDTO(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
