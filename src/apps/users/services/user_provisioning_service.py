import logging

from django.db import transaction

from src.apps.users.dto.user import CreateUserIdentityDTO
from src.apps.users.models import User
from src.apps.users.services.user_service import UserService

logger = logging.getLogger(__name__)


class UserProvisioningService:
    """Point d'intégration unique pour "créer un compte ET lui assigner un
    rôle initial" comme une seule opération métier.

    ⚠️ INTÉGRATION REQUISE CÔTÉ `authentication` : le flux d'inscription
    actuel (que je n'ai pas sous les yeux) crée probablement un `User`
    directement, potentiellement avec un argument `role=...` qui n'existe
    plus sur le modèle depuis cette refactorisation — ce qui casserait à
    l'exécution. Le flux d'inscription doit appeler
    `UserProvisioningService.create_user_with_role(...)` à la place de
    `User.objects.create(...)`. Voir README, section "dépendances à
    corriger".

    Pas de dépendance circulaire : `users` importe `authorization`
    tardivement (à l'intérieur de la méthode, pas en haut de fichier) —
    `authorization` n'a jamais besoin d'importer `users` au niveau Python
    (ses FK vers `users.User` restent des chaînes résolues paresseusement
    par Django).
    """

    @staticmethod
    @transaction.atomic
    def create_user_with_role(
        identity_dto: CreateUserIdentityDTO, role_code: str, assigned_by: User | None = None
    ) -> User:
        from src.apps.authorization.services.role_assignment_service import (
            RoleAssignmentService,
        )

        user = UserService.create_identity(identity_dto)
        RoleAssignmentService.assign_role(user, role_code, assigned_by=assigned_by)

        logger.info(
            "user_provisioned_with_role",
            extra={"user_id": user.pk, "role_code": role_code},
        )
        return user
