import pytest

from src.apps.users.dto.user import CreateUserDTO
from src.apps.users.exceptions.user_exceptions import (
    CannotDeactivateSelfException,
    CannotDeleteSelfException,
    UserAlreadyActiveException,
    UserAlreadyDeactivatedException,
    UserAlreadyDeletedException,
    UserNotDeletedException,
    UserNotFoundException,
)
from src.apps.users.services.user_lifecycle_service import UserLifecycleService
from src.apps.users.services.user_service import UserService


@pytest.mark.django_db
def test_deactivate_and_activate_user():
    user = UserService.create_user(CreateUserDTO(email="lifecycle@example.com", password="password12345"))
    admin = UserService.create_user(CreateUserDTO(email="admin.lifecycle@example.com", password="password12345"))

    # Deactivate
    deactivated = UserLifecycleService.deactivate_user(user.pubkey, actor=admin, reason="Maintenance")
    assert deactivated.is_active is False

    # Deactivate again raises
    with pytest.raises(UserAlreadyDeactivatedException):
        UserLifecycleService.deactivate_user(user.pubkey, actor=admin)

    # Activate
    activated = UserLifecycleService.activate_user(user.pubkey, actor=admin)
    assert activated.is_active is True

    # Activate again raises
    with pytest.raises(UserAlreadyActiveException):
        UserLifecycleService.activate_user(user.pubkey, actor=admin)


@pytest.mark.django_db
def test_cannot_deactivate_self():
    user = UserService.create_user(CreateUserDTO(email="self.deactivate@example.com", password="password12345"))
    with pytest.raises(CannotDeactivateSelfException):
        UserLifecycleService.deactivate_user(user.pubkey, actor=user)


@pytest.mark.django_db
def test_soft_delete_and_restore_user():
    user = UserService.create_user(CreateUserDTO(email="delete.restore@example.com", password="password12345"))
    admin = UserService.create_user(CreateUserDTO(email="admin.del@example.com", password="password12345"))

    # Soft delete
    deleted = UserLifecycleService.soft_delete_user(user.pubkey, actor=admin, reason="RGPD request")
    assert deleted.is_deleted is True
    assert deleted.is_active is False

    # Soft delete again raises
    with pytest.raises(UserAlreadyDeletedException):
        UserLifecycleService.soft_delete_user(user.pubkey, actor=admin)

    # Restore
    restored = UserLifecycleService.restore_user(user.pubkey, actor=admin)
    assert restored.is_deleted is False
    assert restored.is_active is True

    # Restore when not deleted raises
    with pytest.raises(UserNotDeletedException):
        UserLifecycleService.restore_user(user.pubkey, actor=admin)


@pytest.mark.django_db
def test_cannot_delete_self():
    user = UserService.create_user(CreateUserDTO(email="self.delete@example.com", password="password12345"))
    with pytest.raises(CannotDeleteSelfException):
        UserLifecycleService.soft_delete_user(user.pubkey, actor=user)


@pytest.mark.django_db
def test_lifecycle_non_existent_user_raises():
    with pytest.raises(UserNotFoundException):
        UserLifecycleService.activate_user("usr_nonexistent")

    with pytest.raises(UserNotFoundException):
        UserLifecycleService.deactivate_user("usr_nonexistent")

    with pytest.raises(UserNotFoundException):
        UserLifecycleService.soft_delete_user("usr_nonexistent")

    with pytest.raises(UserNotFoundException):
        UserLifecycleService.restore_user("usr_nonexistent")
