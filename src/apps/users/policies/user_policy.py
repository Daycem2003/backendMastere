from src.apps.authorization.services.authorization_service import AuthorizationService


class UserPolicy:
    @staticmethod
    def can_view(requester, target) -> bool:
        if requester.pk == target.pk:
            return True
        return AuthorizationService.has_role(requester.pubkey, "ADMIN")

    @staticmethod
    def can_deactivate(requester, target) -> bool:
        if requester.pk == target.pk:
            return False  # cf. CannotDeactivateSelf
        return AuthorizationService.has_role(requester.pubkey, "ADMIN")

    # `can_assign_role` retiré : l'assignation de rôle est désormais une
    # décision exclusive du module `authorization` (voir
    # authorization_patch/services/role_assignment_service.py).
