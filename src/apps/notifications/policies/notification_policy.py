from src.apps.authorization.services.authorization_service import AuthorizationService


class NotificationPolicy:
    @staticmethod
    def can_send(user) -> bool:
        return AuthorizationService.has_role(user.pubkey, "ADMIN") or AuthorizationService.has_role(
            user.pubkey, "COORDINATOR"
        )

    @staticmethod
    def can_view(user, notification) -> bool:
        if notification.candidate_profile.user_id == user.pk:
            return True
        return NotificationPolicy.can_send(user)
