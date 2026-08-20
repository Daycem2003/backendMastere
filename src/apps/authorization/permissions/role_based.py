from fastapi import Depends
from asgiref.sync import sync_to_async

from src.fastapi_app.legacy_auth import get_current_user
from src.apps.authentication.models import UserModel
from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException
from src.apps.authorization.models import UserRole


def require_roles(*allowed_roles: str):
    """
    Usage :
        @router.get("/admin-only")
        async def endpoint(user: UserModel = Depends(require_roles("ADMIN"))):
            ...
    """

    async def _dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if hasattr(current_user, "pk"):
            has_role = await sync_to_async(
                UserRole.objects.filter(user=current_user, role__code__in=allowed_roles).exists
            )()
        else:
            has_role = getattr(current_user, "role", None) in allowed_roles
        if not has_role:
            raise InsufficientPermissionsException()
        return current_user

    return _dependency
