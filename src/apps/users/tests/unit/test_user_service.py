import pytest

from src.apps.users.dto.user import ChangePasswordDTO, CreateUserDTO, UpdateUserDTO
from src.apps.users.exceptions.user_exceptions import (
    InvalidCurrentPasswordException,
    UserAlreadyExistsException,
)
from src.apps.users.services.user_service import UserService


@pytest.mark.django_db
def test_create_user_success():
    dto = CreateUserDTO(email="john.doe@example.com", password="password12345")
    user = UserService.create_user(dto)

    assert user.pk is not None
    assert user.pubkey.startswith("usr_")
    assert user.email == "john.doe@example.com"
    assert user.is_active is True
    assert user.deleted_at is None
    assert user.role == "CANDIDATE"


@pytest.mark.django_db
def test_create_user_duplicate_email_raises():
    dto1 = CreateUserDTO(email="duplicate@example.com", password="password12345")
    UserService.create_user(dto1)

    dto2 = CreateUserDTO(email="DUPLICATE@example.com", password="password67890")
    with pytest.raises(UserAlreadyExistsException):
        UserService.create_user(dto2)


@pytest.mark.django_db
def test_update_user_email_success():
    user = UserService.create_user(CreateUserDTO(email="initial@example.com", password="password12345"))
    updated = UserService.update_user(user, UpdateUserDTO(email="updated@example.com"))

    assert updated.email == "updated@example.com"


@pytest.mark.django_db
def test_update_user_duplicate_email_raises():
    UserService.create_user(CreateUserDTO(email="user1@example.com", password="password12345"))
    user2 = UserService.create_user(CreateUserDTO(email="user2@example.com", password="password12345"))

    with pytest.raises(UserAlreadyExistsException):
        UserService.update_user(user2, UpdateUserDTO(email="user1@example.com"))


@pytest.mark.django_db
def test_change_password_success():
    user = UserService.create_user(CreateUserDTO(email="pwdtest@example.com", password="old_password_123"))
    UserService.change_password(user, ChangePasswordDTO(old_password="old_password_123", new_password="new_password_456"))

    from src.apps.authentication.services.password_service import PasswordService
    assert PasswordService.verify_password("new_password_456", user.password) is True


@pytest.mark.django_db
def test_change_password_invalid_old_password_raises():
    user = UserService.create_user(CreateUserDTO(email="pwdwrong@example.com", password="old_password_123"))

    with pytest.raises(InvalidCurrentPasswordException):
        UserService.change_password(user, ChangePasswordDTO(old_password="wrong_password", new_password="new_password_456"))
