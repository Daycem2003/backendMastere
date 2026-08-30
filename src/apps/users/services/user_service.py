import logging
import uuid

from django.db import IntegrityError, transaction

from src.apps.authentication.services.password_service import PasswordService
from src.apps.users.dto.user import ChangePasswordDTO, CreateUserDTO, UpdateUserDTO
from src.apps.users.exceptions.user_exceptions import (
    InvalidCurrentPasswordException,
    SamePasswordException,
    UserAlreadyExistsException,
)
from src.apps.users.models import User
from src.apps.users.selectors.user_selector import get_user_by_email

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    @transaction.atomic
    def create_user(dto: CreateUserDTO) -> User:
        """Create a new user in the system domain."""
        existing = get_user_by_email(dto.email, include_deleted=True)
        if existing:
            raise UserAlreadyExistsException()

        pubkey = f"usr_{uuid.uuid4().hex[:20]}"
        hashed_password = PasswordService.hash_password(dto.password)

        try:
            user = User.objects.create(
                pubkey=pubkey,
                email=dto.email,
                password=hashed_password,
                role=dto.role,
                is_active=dto.is_active,
            )
        except IntegrityError as exc:
            raise UserAlreadyExistsException() from exc

        logger.info(
            "user_created",
            extra={"user_pubkey": user.pubkey, "email": user.email},
        )
        return user

    @staticmethod
    @transaction.atomic
    def update_user(user: User, dto: UpdateUserDTO) -> User:
        """Update user domain fields."""
        if dto.email and dto.email != user.email:
            existing = get_user_by_email(dto.email, include_deleted=True)
            if existing and existing.pk != user.pk:
                raise UserAlreadyExistsException()
            user.email = dto.email

        user.save()
        logger.info(
            "user_updated",
            extra={"user_pubkey": user.pubkey, "email": user.email},
        )
        return user

    @staticmethod
    @transaction.atomic
    def change_password(user: User, dto: ChangePasswordDTO) -> User:
        """Change a user's password with verification of old password."""
        if not PasswordService.verify_password(dto.old_password, user.password):
            raise InvalidCurrentPasswordException()

        if dto.old_password == dto.new_password:
            raise SamePasswordException()

        user.password = PasswordService.hash_password(dto.new_password)
        user.save(update_fields=["password", "updated_at"])

        logger.info(
            "user_password_changed",
            extra={"user_pubkey": user.pubkey},
        )
        return user
