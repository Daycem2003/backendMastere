from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService


class CanSendNotifications(BasePermission):
    """Coordinateur ou admin peuvent notifier un candidat."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                AuthorizationService.has_role(request.user.pubkey, "COORDINATOR")
                or AuthorizationService.has_role(request.user.pubkey, "ADMIN")
            )
        )


class IsNotificationRecipient(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.candidate_profile.user_id == request.user.pk
        )


class CanBroadcastNotifications(BasePermission):
    """Seul un admin peut diffuser des annonces avec ciblage."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "administrateur", None) is not None
                or getattr(request.user, "is_staff", False)
                or AuthorizationService.has_role(request.user.pubkey, "ADMIN")
            )
        )

