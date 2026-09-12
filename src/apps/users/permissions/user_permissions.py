from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user and request.user.is_authenticated and obj.pk == request.user.pk
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and AuthorizationService.has_role(request.user.pubkey, "ADMIN")
        )
