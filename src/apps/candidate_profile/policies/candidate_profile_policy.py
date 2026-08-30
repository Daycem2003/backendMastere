from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.candidate_profile.models import CandidateStatus


class CandidateProfilePolicy:
    @staticmethod
    def can_view(user, profile) -> bool:
        if profile.user_id == user.pk:
            return True
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or AuthorizationService.has_role(
            user.pubkey, "COORDINATOR"
        )

    @staticmethod
    def can_edit(user, profile) -> bool:
        """Un candidat ne peut modifier son profil que tant qu'il n'a pas
        été validé (une fois VALIDE, les pièces ont été vérifiées par un
        coordinateur — toute modification doit repasser par une demande
        explicite, pas une édition libre)."""
        if profile.user_id != user.pk:
            return False
        return profile.statut != CandidateStatus.VALIDE
