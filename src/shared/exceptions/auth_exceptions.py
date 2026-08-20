from rest_framework.exceptions import APIException, AuthenticationFailed, NotFound, PermissionDenied, ValidationError


class InvalidCredentialsException(AuthenticationFailed):
    default_detail = "Email ou mot de passe incorrect."


class EmailAlreadyExistsException(APIException):
    status_code = 409
    default_detail = "Un compte existe déjà avec cet email."


class InvalidTokenException(AuthenticationFailed):
    default_detail = "Token invalide ou expiré."


class InvalidOtpException(ValidationError):
    default_detail = "Code de vérification invalide ou expiré."


class UserNotFoundException(NotFound):
    default_detail = "Utilisateur introuvable."


class InactiveUserException(PermissionDenied):
    default_detail = "Ce compte est désactivé."


class InsufficientPermissionsException(PermissionDenied):
    default_detail = "Vous n'avez pas les permissions nécessaires pour cette action."
