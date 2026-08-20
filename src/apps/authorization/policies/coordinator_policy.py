from src.apps.authentication.models import UserModel
from src.apps.authorization.services.authorization_service import AuthorizationService


class CoordinatorPolicy:
    """
    Un coordinateur n'a de droits que sur les Masters dont il est le
    `coordinateurId`, et par extension sur les Applications qui ciblent ces
    Masters. `master_coordinateur_user_id` est l'`userId` du Coordinateur
    propriétaire du master (déjà résolu par l'appelant via un selector, pas
    de requête DB ici).
    """

    @staticmethod
    def owns_master(user: UserModel, master_coordinateur_user_id: int) -> bool:
        return user.id == master_coordinateur_user_id

    @classmethod
    def can_manage_master(cls, user: UserModel, master_coordinateur_user_id: int) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or (
            AuthorizationService.has_role(user.pubkey, "COORDINATOR")
            and cls.owns_master(user, master_coordinateur_user_id)
        )

    @classmethod
    def can_view_applications(cls, user: UserModel, master_coordinateur_user_id: int) -> bool:
        return cls.can_manage_master(user, master_coordinateur_user_id)

    @classmethod
    def can_review_application(cls, user: UserModel, master_coordinateur_user_id: int) -> bool:
        return cls.can_manage_master(user, master_coordinateur_user_id)
