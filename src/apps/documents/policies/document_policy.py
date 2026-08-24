from src.apps.authorization.services.authorization_service import AuthorizationService


class DocumentPolicy:
    @staticmethod
    def can_review(user) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or AuthorizationService.has_role(
            user.pubkey, "COORDINATOR"
        )

    @staticmethod
    def can_view_candidate_documents(user, candidate_profile) -> bool:
        if candidate_profile.user_id == user.pk:
            return True
        return DocumentPolicy.can_review(user)
