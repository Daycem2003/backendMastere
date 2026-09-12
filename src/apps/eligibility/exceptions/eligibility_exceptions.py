from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError


class EligibilityRuleNotFound(NotFound):
    default_detail = "Règle d'éligibilité introuvable."


class InvalidRuleConfiguration(ValidationError):
    default_detail = "Configuration de règle invalide."


class EligibilityAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à gérer les règles d'éligibilité de ce master."


class LicenceTypeNotAcceptedByMaster(ValidationError):
    default_detail = "Ce type de licence n'est pas accepté par ce master."
