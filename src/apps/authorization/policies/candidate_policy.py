from src.apps.authentication.models import UserModel
from src.apps.authorization.services.authorization_service import AuthorizationService


class CandidatePolicy:
    """
    Règles d'ownership pures pour l'entité CandidateProfile. Ne fait aucun
    accès DB : `profile` doit déjà être chargé (avec son `userId`) par
    l'appelant (généralement un selector de l'app candidate_profile).
    """

    @staticmethod
    def is_owner(user: UserModel, profile_user_id: int) -> bool:
        return user.id == profile_user_id

    @classmethod
    def can_view(cls, user: UserModel, profile_user_id: int) -> bool:
        return (
            AuthorizationService.has_role(user.pubkey, "ADMIN")
            or AuthorizationService.has_role(user.pubkey, "COORDINATOR")
            or cls.is_owner(user, profile_user_id)
        )

    @classmethod
    def can_update(cls, user: UserModel, profile_user_id: int) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or cls.is_owner(
            user, profile_user_id
        )

    @classmethod
    def can_delete(cls, user: UserModel, profile_user_id: int) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN")
