from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService


class CanManageEligibilityRules(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                AuthorizationService.has_role(request.user.pubkey, "COORDINATOR")
                or AuthorizationService.has_role(request.user.pubkey, "ADMIN")
            )
        )

    def has_object_permission(self, request, view, obj) -> bool:
        if AuthorizationService.has_role(request.user.pubkey, "ADMIN"):
            return True
        coordinateur = getattr(request.user, "coordinateur", None)
        return bool(coordinateur and obj.master.coordinateur_id == coordinateur.id)
