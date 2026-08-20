from fastapi import Depends

from src.fastapi_app.legacy_auth import get_current_user
from src.apps.authentication.models import UserModel
from src.apps.authorization.services.authorization_service import AuthorizationService


def require_permission(permission_code: str):
    """
    Usage :
        @router.post("/masters")
        async def create_master(
            user: UserModel = Depends(require_permission(P.MASTER_CREATE)),
        ):
            ...
    """

    async def _dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        await AuthorizationService.check_or_raise(current_user.pubkey, permission_code)
        return current_user

    return _dependency


def require_any_permission(*permission_codes: str):
    async def _dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException

        if not await AuthorizationService.user_has_any_permission(
            current_user.pubkey, list(permission_codes)
        ):
            raise InsufficientPermissionsException()
        return current_user

    return _dependency
