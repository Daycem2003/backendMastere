from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.users.policies.user_policy import UserPolicy


class CanListUsersPermission(BasePermission):
    """Permission to list all users (ADMIN or COORDINATOR)."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        return UserPolicy.can_list_users(request.user)


class CanManageUserLifecyclePermission(BasePermission):
    """Permission to manage user lifecycle (ADMIN only)."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        return AuthorizationService.has_role(request.user.pubkey, "ADMIN")


class IsSelfOrAdminPermission(BasePermission):
    """Permission allowing the user himself or an ADMIN."""

    def has_object_permission(self, request, view, obj) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        return UserPolicy.can_update_user(request.user, obj)
