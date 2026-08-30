from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)


class UserNotFoundException(NotFound):
    default_detail = "Utilisateur introuvable."


class UserAlreadyExistsException(ValidationError):
    default_detail = "Un utilisateur avec cet email existe déjà."


class UserAlreadyActiveException(ValidationError):
    default_detail = "Le compte utilisateur est déjà actif."


class UserAlreadyDeactivatedException(ValidationError):
    default_detail = "Le compte utilisateur est déjà désactivé."


class UserAlreadyDeletedException(ValidationError):
    default_detail = "Le compte utilisateur est déjà supprimé."


class UserNotDeletedException(ValidationError):
    default_detail = "Le compte utilisateur n'est pas marqué comme supprimé."


class UserAccessDeniedException(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à accéder à cette ressource utilisateur."


class InvalidCurrentPasswordException(ValidationError):
    default_detail = "Le mot de passe actuel est incorrect."


class SamePasswordException(ValidationError):
    default_detail = "Le nouveau mot de passe doit être différent de l'ancien."


class CannotDeactivateSelfException(ValidationError):
    default_detail = "Vous ne pouvez pas désactiver votre propre compte."


class CannotDeleteSelfException(ValidationError):
    default_detail = "Vous ne pouvez pas supprimer votre propre compte."


class InvalidUserOperationException(APIException):
    status_code = 400
    default_detail = "Opération invalide sur le compte utilisateur."
