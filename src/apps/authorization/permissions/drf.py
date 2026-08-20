from rest_framework.permissions import BasePermission

from src.apps.authorization.services.authorization_service import AuthorizationService


class HasPermission(BasePermission):
    required_permission: str | None = None

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        permission_code = self.required_permission or getattr(view, "required_permission", None)
        if not permission_code:
            return False
        return AuthorizationService.has_permission(
            request.user.pubkey, permission_code
        )


def require_permission(permission_code: str):
    return type(
        f"HasPermission_{permission_code.replace(':', '_')}",
        (HasPermission,),
        {"required_permission": permission_code},
    )


class HasRole(BasePermission):
    required_role: str | None = None

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        role_code = self.required_role or getattr(view, "required_role", None)
        if not role_code:
            return False
        from src.apps.authorization.models import UserRole

        return UserRole.objects.filter(
            user_id=request.user.pk, role__code=role_code
        ).exists()


def require_role(role_code: str):
    return type(
        f"HasRole_{role_code}",
        (HasRole,),
        {"required_role": role_code},
    )


class HasAnyPermission(BasePermission):
    required_permissions: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        permissions = self.required_permissions or tuple(
            getattr(view, "required_permissions", ())
        )
        return AuthorizationService.has_any_permission(
            request.user.pubkey, list(permissions)
        )


class HasAllPermissions(BasePermission):
    required_permissions: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        permissions = self.required_permissions or tuple(
            getattr(view, "required_permissions", ())
        )
        return AuthorizationService.has_all_permissions(
            request.user.pubkey, list(permissions)
        )


class IsOwner(BasePermission):
    owner_attribute = "user_id"

    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(obj, self.owner_attribute, None) == request.user.pk
        )
