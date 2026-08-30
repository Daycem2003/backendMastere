import logging

from django.db import transaction
from django.utils import timezone

from src.apps.users.exceptions.user_exceptions import (
    CannotDeactivateSelfException,
    CannotDeleteSelfException,
    UserAlreadyActiveException,
    UserAlreadyDeactivatedException,
    UserAlreadyDeletedException,
    UserNotDeletedException,
    UserNotFoundException,
)
from src.apps.users.models import User
from src.apps.users.selectors.user_selector import get_user_by_pubkey

logger = logging.getLogger(__name__)


class UserLifecycleService:
    @staticmethod
    @transaction.atomic
    def activate_user(user_pubkey: str, actor: User | None = None) -> User:
        """Activate a user account."""
        user = get_user_by_pubkey(user_pubkey, include_deleted=True)
        if not user:
            raise UserNotFoundException()

        if user.is_active and not user.is_deleted:
            raise UserAlreadyActiveException()

        user.is_active = True
        user.deleted_at = None
        user.save(update_fields=["is_active", "deleted_at", "updated_at"])

        logger.info(
            "user_activated",
            extra={
                "user_pubkey": user.pubkey,
                "actor_pubkey": actor.pubkey if actor else None,
            },
        )
        return user

    @staticmethod
    @transaction.atomic
    def deactivate_user(
        user_pubkey: str,
        actor: User | None = None,
        reason: str | None = None,
    ) -> User:
        """Deactivate a user account."""
        user = get_user_by_pubkey(user_pubkey, include_deleted=False)
        if not user:
            raise UserNotFoundException()

        if actor and actor.pubkey == user.pubkey:
            raise CannotDeactivateSelfException()

        if not user.is_active:
            raise UserAlreadyDeactivatedException()

        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])

        logger.info(
            "user_deactivated",
            extra={
                "user_pubkey": user.pubkey,
                "actor_pubkey": actor.pubkey if actor else None,
                "reason": reason,
            },
        )
        return user

    @staticmethod
    @transaction.atomic
    def soft_delete_user(
        user_pubkey: str,
        actor: User | None = None,
        reason: str | None = None,
    ) -> User:
        """Soft-delete a user account."""
        user = get_user_by_pubkey(user_pubkey, include_deleted=True)
        if not user:
            raise UserNotFoundException()

        if actor and actor.pubkey == user.pubkey:
            raise CannotDeleteSelfException()

        if user.is_deleted:
            raise UserAlreadyDeletedException()

        user.deleted_at = timezone.now()
        user.is_active = False
        user.save(update_fields=["deleted_at", "is_active", "updated_at"])

        logger.info(
            "user_soft_deleted",
            extra={
                "user_pubkey": user.pubkey,
                "actor_pubkey": actor.pubkey if actor else None,
                "reason": reason,
            },
        )
        return user

    @staticmethod
    @transaction.atomic
    def restore_user(user_pubkey: str, actor: User | None = None) -> User:
        """Restore a soft-deleted user account."""
        user = get_user_by_pubkey(user_pubkey, include_deleted=True)
        if not user:
            raise UserNotFoundException()

        if not user.is_deleted:
            raise UserNotDeletedException()

        user.deleted_at = None
        user.is_active = True
        user.save(update_fields=["deleted_at", "is_active", "updated_at"])

        logger.info(
            "user_restored",
            extra={
                "user_pubkey": user.pubkey,
                "actor_pubkey": actor.pubkey if actor else None,
            },
        )
        return user
