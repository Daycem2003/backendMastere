from rest_framework.exceptions import APIException, NotFound, PermissionDenied


class RoleNotFoundException(NotFound):
    default_detail = "Rôle introuvable."


class PermissionNotFoundException(NotFound):
    default_detail = "Permission introuvable."


class PermissionDeniedException(PermissionDenied):
    def __init__(self, required_permission: str | None = None):
        detail = "Action non autorisée."
        if required_permission:
            detail = f"Action non autorisée (permission requise : {required_permission})."
        super().__init__(detail)


class RoleAlreadyExistsException(APIException):
    status_code = 409
    default_detail = "Ce rôle existe déjà."


class CannotModifySystemRoleException(PermissionDenied):
    default_detail = "Ce rôle système ne peut pas être modifié ou supprimé."


class RoleAssignmentAlreadyExistsException(APIException):
    status_code = 409
    default_detail = "Ce rôle est déjà assigné à cet utilisateur."


class RoleAssignmentNotFoundException(NotFound):
    default_detail = "Cette assignation de rôle n'existe pas."


class PrivilegeEscalationException(PermissionDenied):
    default_detail = "Cette auto-attribution de rôle privilégié est interdite."
