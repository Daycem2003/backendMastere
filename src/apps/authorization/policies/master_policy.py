from src.apps.authentication.models import UserModel
from src.apps.authorization.services.authorization_service import AuthorizationService


class MasterPolicy:
    """
    `owner_user_id` = userId du Coordinateur propriétaire du Master
    (résolu par l'appelant, ex: apps/masters/selectors).
    `master_status` = valeur brute de Master.statut ("OUVERT"/"FERME"/"BROUILLON").
    """

    @staticmethod
    def can_create(user: UserModel) -> bool:
        return AuthorizationService.has_role(user.pubkey, "COORDINATOR") or AuthorizationService.has_role(
            user.pubkey, "ADMIN"
        )

    @staticmethod
    def _is_owner_or_admin(user: UserModel, owner_user_id: int) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or user.id == owner_user_id

    @classmethod
    def can_update(cls, user: UserModel, owner_user_id: int) -> bool:
        return cls._is_owner_or_admin(user, owner_user_id)

    @classmethod
    def can_delete(cls, user: UserModel, owner_user_id: int) -> bool:
        return cls._is_owner_or_admin(user, owner_user_id)

    @classmethod
    def can_publish(cls, user: UserModel, owner_user_id: int) -> bool:
        return cls._is_owner_or_admin(user, owner_user_id)

    @classmethod
    def can_view(cls, user: UserModel | None, owner_user_id: int, master_status: str) -> bool:
        """
        Un master BROUILLON n'est visible que par son propriétaire ou un
        ADMIN. Un master OUVERT/FERME est public (même utilisateur anonyme,
        `user=None`, ex: landing page publique).
        """
        if master_status != "BROUILLON":
            return True
        if user is None:
            return False
        return cls._is_owner_or_admin(user, owner_user_id)
