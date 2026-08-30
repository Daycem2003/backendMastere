from asgiref.sync import sync_to_async
from fastapi import Depends

from src.apps.authentication.models import UserModel
from src.apps.authorization.models import UserRole
from src.fastapi_app.legacy_auth import get_current_user
from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException


def require_roles(*allowed_roles: str):
    """
    Usage :
        @router.get("/admin-only")
        async def endpoint(user: UserModel = Depends(require_roles("ADMIN"))):
            ...
    """

    async def _dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        user_pubkey = getattr(current_user, "pubkey", None)
        if not user_pubkey:
            raise InsufficientPermissionsException()
        has_role = await sync_to_async(
            UserRole.objects.filter(user__pubkey=user_pubkey, role__code__in=allowed_roles).exists
        )()
        if not has_role:
            raise InsufficientPermissionsException()
        return current_user

    return _dependency
