from asgiref.sync import sync_to_async

from src.apps.authorization.selectors.authorization_selector import get_effective_permission_codes
from src.apps.authorization.models import UserRole
from src.apps.authorization.exceptions.authorization_exceptions import PermissionDeniedException


class AuthorizationService:
    """
    Point d'entrée UNIQUE pour vérifier si un utilisateur a une permission
    donnée. Toute autre couche (dependencies FastAPI, policies) doit passer
    par ici plutôt que de relire les tables AUTH_* directement.
    """

    @staticmethod
    def has_permission(user_pubkey: str, permission_code: str) -> bool:
        return UserRole.objects.filter(
            user__pubkey=user_pubkey,
            role__role_permissions__permission__code=permission_code,
        ).exists()

    @staticmethod
    def has_role(user_pubkey: str, role_code: str) -> bool:
        return UserRole.objects.filter(
            user__pubkey=user_pubkey, role__code=role_code
        ).exists()

    @staticmethod
    def has_any_permission(user_pubkey: str, permission_codes: list[str]) -> bool:
        return UserRole.objects.filter(
            user__pubkey=user_pubkey,
            role__role_permissions__permission__code__in=permission_codes,
        ).exists()

    @staticmethod
    def has_all_permissions(user_pubkey: str, permission_codes: list[str]) -> bool:
        if not permission_codes:
            return True
        granted = UserRole.objects.filter(
            user__pubkey=user_pubkey,
            role__role_permissions__permission__code__in=permission_codes,
        ).values_list("role__role_permissions__permission__code", flat=True).distinct()
        return set(permission_codes).issubset(granted)

    @staticmethod
    async def user_has_permission(user_pubkey: str, permission_code: str) -> bool:
        codes = await sync_to_async(get_effective_permission_codes)(user_pubkey)
        return permission_code in codes

    @staticmethod
    async def user_has_any_permission(user_pubkey: str, permission_codes: list[str]) -> bool:
        codes = await sync_to_async(get_effective_permission_codes)(user_pubkey)
        return bool(codes.intersection(permission_codes))

    @staticmethod
    async def user_has_all_permissions(user_pubkey: str, permission_codes: list[str]) -> bool:
        codes = await sync_to_async(get_effective_permission_codes)(user_pubkey)
        return set(permission_codes).issubset(codes)

    @classmethod
    async def check_or_raise(cls, user_pubkey: str, permission_code: str) -> None:
        if not await cls.user_has_permission(user_pubkey, permission_code):
            raise PermissionDeniedException(required_permission=permission_code)
