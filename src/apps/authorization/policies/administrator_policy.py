from src.apps.authentication.models import UserModel
from src.apps.authorization.services.authorization_service import AuthorizationService


class AdministratorPolicy:
    """
    Un ADMIN a un accès global à toutes les entités du domaine, y compris la
    gestion des rôles/permissions eux-mêmes (contrairement au coordinateur,
    scoppé à ses propres masters).
    """

    @staticmethod
    def is_admin(user: UserModel) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN")

    @classmethod
    def can_manage_roles(cls, user: UserModel) -> bool:
        return cls.is_admin(user)

    @classmethod
    def can_manage_any_master(cls, user: UserModel) -> bool:
        return cls.is_admin(user)

    @classmethod
    def can_view_any_candidate_profile(cls, user: UserModel) -> bool:
        return cls.is_admin(user)
