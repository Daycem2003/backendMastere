from pydantic import BaseModel, Field, field_validator


class CreateCandidateProfileDTO(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    cin: str = Field(min_length=8, max_length=20)
    nationalite: str = Field(min_length=1, max_length=100)

    email: str
    telephone: str = Field(min_length=6, max_length=20)
    ville: str = Field(min_length=1, max_length=100)
    annee_naissance: int

    @field_validator("annee_naissance")
    @classmethod
    def annee_plausible(cls, v: int) -> int:
        if not (1940 <= v <= 2015):
            raise ValueError("Année de naissance invalide.")
        return v


class UpdateCandidateProfileDTO(BaseModel):
    telephone: str | None = Field(default=None, min_length=6, max_length=20)
    nationalite: str | None = Field(default=None, min_length=1, max_length=100)
    ville: str | None = Field(default=None, min_length=1, max_length=100)


class CreateLicenceYearDTO(BaseModel):
    type_licence_pubkey: str
    annee: int
    annee_universitaire: str = Field(min_length=4, max_length=20)
    moyenne: float = Field(ge=0, le=20)


class CreateDiplomeDTO(BaseModel):
    type_licence_pubkey: str
    annee_obtention: str
    universite: str = Field(min_length=1, max_length=200)


class CreateMaster1YearDTO(BaseModel):
    annee_universitaire: str = Field(min_length=4, max_length=20)
    moyenne: float = Field(ge=0, le=20)
    etablissement: str = Field(min_length=1, max_length=200)
    master_pubkey: str | None = None  # renseigné si le M1 a été fait sur un Master de la plateforme


class SetRedoublementDTO(BaseModel):
    a_redouble: bool
    annees: list[str] = Field(default_factory=list)
