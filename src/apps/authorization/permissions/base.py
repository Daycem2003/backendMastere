from abc import ABC, abstractmethod

from src.apps.authentication.models import UserModel


class BasePermissionDependency(ABC):
    """
    Contrat commun pour les dépendances de permissions (role_based.py,
    permission_based.py). Une implémentation concrète expose `__call__` pour
    être directement injectable via `Depends(...)` par FastAPI.
    """

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> UserModel: ...
