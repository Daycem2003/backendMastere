from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError


class MasterNotFound(NotFound):
    default_detail = "Master introuvable."


class TypeLicenceNotFound(NotFound):
    default_detail = "Un ou plusieurs types de licence sont introuvables."


class MasterAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à gérer ce master."


class MasterNotEditable(APIException):
    status_code = 400
    default_detail = "Ce master ne peut plus être modifié dans son état actuel (candidatures déjà ouvertes)."


class InvalidPasserelleTarget(ValidationError):
    default_detail = "Un master ne peut pas avoir de passerelle vers lui-même."


class ScoreFormulaAlreadyExists(ValidationError):
    default_detail = "Une formule de score existe déjà pour ce master."
