from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.users.models import User


class UserPolicy:
    @staticmethod
    def can_view_user(actor: User, target_user: User) -> bool:
        """Check if actor is allowed to view target user's details."""
        if not actor or not actor.is_authenticated:
            return False
        if actor.pk == target_user.pk or actor.pubkey == target_user.pubkey:
            return True
        return AuthorizationService.has_role(actor.pubkey, "ADMIN") or AuthorizationService.has_role(
            actor.pubkey, "COORDINATOR"
        )

    @staticmethod
    def can_list_users(actor: User) -> bool:
        """Check if actor is allowed to list users in the system."""
        if not actor or not actor.is_authenticated:
            return False
        return AuthorizationService.has_role(actor.pubkey, "ADMIN") or AuthorizationService.has_role(
            actor.pubkey, "COORDINATOR"
        )

    @staticmethod
    def can_update_user(actor: User, target_user: User) -> bool:
        """Check if actor is allowed to update target user's domain details."""
        if not actor or not actor.is_authenticated:
            return False
        if actor.pk == target_user.pk or actor.pubkey == target_user.pubkey:
            return True
        return AuthorizationService.has_role(actor.pubkey, "ADMIN")

    @staticmethod
    def can_manage_user_lifecycle(actor: User, target_user: User) -> bool:
        """Check if actor is allowed to perform lifecycle actions (activate, deactivate, delete, restore)."""
        if not actor or not actor.is_authenticated:
            return False
        return AuthorizationService.has_role(actor.pubkey, "ADMIN")
