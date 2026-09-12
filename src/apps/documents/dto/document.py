from pydantic import BaseModel, Field


class DocumentSlotIdentityDTO(BaseModel):
    """Identifie un slot de façon unique pour un candidat — construit par
    la vue à partir de champs EXPLICITES du client, jamais d'une chaîne
    document_type libre."""

    slot_type: str = Field(min_length=2, max_length=32)
    domaine: str = ""
    annee_licence: str = ""
    redoublement_annee: str = ""
    justificatif_index: int = Field(default=0, ge=0)


class DocumentUploadDTO(BaseModel):
    candidate_profile_pubkey: str
    slot: DocumentSlotIdentityDTO
    storage_key: str = Field(min_length=1)
    mime_type: str = Field(min_length=1, max_length=255)
    file_size: int = Field(ge=0)
    checksum: str = ""


class DocumentRejectionDTO(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)