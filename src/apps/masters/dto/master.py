from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CreateMasterDTO(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    domaine: str = Field(min_length=1, max_length=100)
    discipline: str = Field(min_length=1, max_length=100)
    specialite: str = Field(min_length=1, max_length=200)
    nombre_places: int = Field(gt=0)
    date_debut: datetime
    date_fin: datetime
    type_licence_pubkeys: list[str] = Field(default_factory=list)

    @field_validator("date_fin")
    @classmethod
    def fin_apres_debut(cls, v: datetime, info) -> datetime:
        debut = info.data.get("date_debut")
        if debut and v <= debut:
            raise ValueError("La date de fin doit être postérieure à la date de début.")
        return v


class UpdateMasterDTO(BaseModel):
    nom: str | None = None
    ville: str | None = None
    nombre_places: int | None = Field(default=None, gt=0)
    date_debut: datetime | None = None
    date_fin: datetime | None = None


class SetAcceptedLicenceTypesDTO(BaseModel):
    type_licence_pubkeys: list[str]


class SetPasserellesDTO(BaseModel):
    """Masters M1 depuis lesquels une passerelle vers ce master est ouverte."""

    from_master_pubkeys: list[str]


class AddRequiredDocumentDTO(BaseModel):
    type: str = Field(min_length=1, max_length=50)


class SetScoreFormulaDTO(BaseModel):
    criteria: list["ScoreCriterionDTO"]

    @field_validator("criteria")
    @classmethod
    def poids_positifs(cls, v: list["ScoreCriterionDTO"]) -> list["ScoreCriterionDTO"]:
        if not v:
            raise ValueError("Une formule de score doit contenir au moins un critère.")
        if any(c.poids <= 0 for c in v):
            raise ValueError("Chaque poids doit être strictement positif.")
        return v


class ScoreCriterionDTO(BaseModel):
    critere: str = Field(min_length=1, max_length=100)
    poids: float = Field(gt=0)


SetScoreFormulaDTO.model_rebuild()