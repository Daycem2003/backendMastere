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
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return bool(
            getattr(user, "coordinateur", None) is not None
            or getattr(user, "administrateur", None) is not None
            or AuthorizationService.has_role(user.pubkey, "COORDINATOR")
            or AuthorizationService.has_role(user.pubkey, "ADMIN")
        )
