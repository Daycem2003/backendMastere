from typing import Callable, Awaitable

from fastapi import Depends

from src.apps.authentication.models import UserModel
from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException

PermissionCheck = Callable[[UserModel], Awaitable[bool]]


def any_of(*dependencies):
    """
    Autorise l'accès si AU MOINS UNE des dépendances passées ne lève pas
    d'exception. Usage :

        Depends(any_of(require_roles("ADMIN"), require_permission(P.MASTER_UPDATE)))
    """

    async def _dependency(**kwargs) -> UserModel:
        last_error: Exception | None = None
        for dependency in dependencies:
            try:
                return await dependency(**kwargs)
            except Exception as error:  # noqa: BLE001 - on veut essayer la suivante
                last_error = error
                continue
        if last_error:
            raise last_error
        raise InsufficientPermissionsException()

    return _dependency


def all_of(*dependencies):
    """Autorise l'accès seulement si TOUTES les dépendances passent."""

    async def _dependency(current_user: UserModel = Depends(dependencies[0])) -> UserModel:
        for dependency in dependencies[1:]:
            current_user = await dependency(current_user=current_user)
        return current_user

    return _dependency
