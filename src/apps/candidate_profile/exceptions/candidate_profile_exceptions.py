from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError


class ProfileAlreadyExists(ValidationError):
    default_detail = "Un profil candidat existe déjà pour cet utilisateur."


class CandidateProfileNotFound(NotFound):
    default_detail = "Profil candidat introuvable."


class TypeLicenceNotFound(NotFound):
    default_detail = "Type de licence introuvable."


class TypeLicenceNotEligible(ValidationError):
    default_detail = "Ce type de licence n'est pas éligible."


class DiplomeAlreadyExists(ValidationError):
    default_detail = "Un diplôme a déjà été soumis pour ce profil."


class MasterOriginNotFound(NotFound):
    default_detail = "Le master d'origine indiqué est introuvable."


class ProfileAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à accéder à ce profil."


class ProfileNotEditable(APIException):
    status_code = 400
    default_detail = "Ce profil ne peut plus être modifié dans son état actuel."
