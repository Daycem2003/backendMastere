from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError


class CandidateProfileRequired(APIException):
    status_code = 403
    default_detail = "Vous devez créer votre profil candidat avant de postuler."


class MasterNotFound(NotFound):
    default_detail = "Master introuvable."


class MasterNotOpen(ValidationError):
    default_detail = "Ce master n'est pas ouvert aux candidatures."


class AlreadyApplied(ValidationError):
    default_detail = "Vous avez déjà une candidature active pour ce master."


class NotEligible(ValidationError):
    default_detail = "Vous ne remplissez pas les critères d'éligibilité pour ce master."

    def __init__(self, detail: str | None = None, failed_criteria: list[dict] | None = None):
        if failed_criteria:
            super().__init__(detail={"detail": detail or self.default_detail, "failed_criteria": failed_criteria})
        else:
            super().__init__(detail=detail or self.default_detail)


class MissingRequiredDocuments(ValidationError):
    default_detail = "Des documents requis sont manquants ou non encore approuvés."

    def __init__(self, missing_types: list[str]):
        super().__init__(detail={"detail": self.default_detail, "missing_types": missing_types})


class ApplicationNotFound(NotFound):
    default_detail = "Candidature introuvable."


class ApplicationAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à accéder à cette candidature."


class ApplicationNotWithdrawable(ValidationError):
    default_detail = "Cette candidature ne peut plus être retirée dans son état actuel."


class ApplicationAlreadyDecided(ValidationError):
    default_detail = "Cette candidature a déjà fait l'objet d'une décision."
