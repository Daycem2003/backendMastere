import logging
import uuid

from src.apps.users.dto.user import CreateUserIdentityDTO, SetActiveStatusDTO
from src.apps.users.exceptions.user_exceptions import (
    CannotDeactivateSelf,
    UserAlreadyActive,
    UserAlreadyExists,
    UserAlreadyInactive,
)
from src.apps.users.models import User
from src.apps.users.selectors.user_selector import get_by_email

logger = logging.getLogger(__name__)


class UserService:
    """Identité et cycle de vie du compte uniquement. Aucune méthode ici
    ne lit ni n'écrit de rôle — voir `user_provisioning_service.py` pour
    l'orchestration création + assignation initiale, et
    `authorization_patch/services/role_assignment_service.py` pour tout
    changement de rôle après coup."""

    @staticmethod
    def create_identity(dto: CreateUserIdentityDTO) -> User:
        """Crée uniquement l'identité. N'assigne aucun rôle — c'est la
        responsabilité de l'appelant (voir `UserProvisioningService` pour
        le cas où création + rôle initial forment une seule opération
        métier)."""
        if get_by_email(dto.email):
            raise UserAlreadyExists()

        user = User.objects.create(
            pubkey=f"usr_{uuid.uuid4().hex[:24]}",
            email=dto.email,
            password=dto.password_hash,
        )
        logger.info("user_identity_created", extra={"user_id": user.pk})
        return user

    @staticmethod
    def set_active_status(target: User, dto: SetActiveStatusDTO, actor: User) -> User:
        if target.pk == actor.pk and not dto.is_active:
            raise CannotDeactivateSelf()
        if target.is_active == dto.is_active:
            raise (UserAlreadyActive() if dto.is_active else UserAlreadyInactive())

        target.is_active = dto.is_active
        target.save(update_fields=["is_active"])

        logger.info(
            "user_active_status_changed",
            extra={
                "user_id": target.pk,
                "is_active": dto.is_active,
                "actor_id": actor.pk,
                "reason": dto.reason,
            },
        )
        return target
