from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError


class UserNotFound(NotFound):
    default_detail = "Utilisateur introuvable."


class UserAlreadyExists(ValidationError):
    default_detail = "Un utilisateur existe déjà avec cet email."


class UserAlreadyInactive(ValidationError):
    default_detail = "Ce compte est déjà désactivé."


class UserAlreadyActive(ValidationError):
    default_detail = "Ce compte est déjà actif."


class CannotDeactivateSelf(APIException):
    status_code = 400
    default_detail = "Vous ne pouvez pas désactiver votre propre compte."


class UserAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à accéder à cet utilisateur."
