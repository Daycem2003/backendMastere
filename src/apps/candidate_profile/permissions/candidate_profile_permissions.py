from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService


class IsProfileOwner(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.user_id == request.user.pk
        )


class CanViewAnyProfile(BasePermission):
    """Coordinateur/admin peuvent consulter n'importe quel profil (revue de
    candidature)."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                AuthorizationService.has_role(request.user.pubkey, "COORDINATOR")
                or AuthorizationService.has_role(request.user.pubkey, "ADMIN")
            )
        )
