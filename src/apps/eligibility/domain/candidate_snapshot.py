from datetime import date

from pydantic import BaseModel


class CandidateSnapshot(BaseModel):
    """Vue plate des données du candidat nécessaires à l'évaluation —
    découple `eligibility` du détail des modèles `candidate_profile`
    (faible couplage, cf. spec). Un champ absent (`None`) signifie que la
    donnée n'a pas été soumise par le candidat, pas qu'elle vaut 0/faux."""

    licence_type_code: str | None = None
    licence_type_name: str | None = None
    average: float | None = None
    repeated_years: int | None = None
    nationality: str | None = None
    university_name: str | None = None
    graduation_date: date | None = None
    date_of_birth: date | None = None
