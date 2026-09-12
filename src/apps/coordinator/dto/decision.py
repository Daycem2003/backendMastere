from pydantic import BaseModel, Field, model_validator


class RejectCandidatureDTO(BaseModel):
    motif: str | None = None


class RequestRevisionDTO(BaseModel):
    message: str | None = Field(default="", description="Message ou champs à corriger")
    documents_a_redeposer: list[str] = Field(
        default_factory=list,
        description="Liste des identifiants (pubkeys) des documents ou slots à redéposer",
    )

    @model_validator(mode="after")
    def validate_content(self):
        msg = (self.message or "").strip()
        if not msg and not self.documents_a_redeposer:
            raise ValueError(
                "Veuillez saisir un message explicatif ou sélectionner au moins un document à redéposer."
            )
        return self
