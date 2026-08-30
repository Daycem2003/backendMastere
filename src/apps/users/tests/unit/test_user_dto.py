import pytest
from pydantic import ValidationError

from src.apps.users.dto.user import (
    ChangePasswordDTO,
    CreateUserDTO,
    UpdateUserDTO,
    UserFilterDTO,
)


def test_create_user_dto_normalizes_email():
    dto = CreateUserDTO(email="  TEST.User@Example.Com  ", password="strongpassword123")
    assert dto.email == "test.user@example.com"
    assert dto.password == "strongpassword123"
    assert dto.role == "CANDIDATE"
    assert dto.is_active is True


def test_create_user_dto_invalid_email():
    with pytest.raises(ValidationError):
        CreateUserDTO(email="not-an-email", password="strongpassword123")


def test_create_user_dto_short_password():
    with pytest.raises(ValidationError):
        CreateUserDTO(email="valid@example.com", password="short")


def test_update_user_dto_normalizes_email():
    dto = UpdateUserDTO(email="  NewEmail@Domain.Com ")
    assert dto.email == "newemail@domain.com"


def test_update_user_dto_none_email():
    dto = UpdateUserDTO()
    assert dto.email is None


def test_change_password_dto_valid():
    dto = ChangePasswordDTO(old_password="old_pass_123", new_password="new_pass_456")
    assert dto.old_password == "old_pass_123"
    assert dto.new_password == "new_pass_456"


def test_change_password_dto_same_password_rejected():
    with pytest.raises(ValidationError):
        ChangePasswordDTO(old_password="same_password_123", new_password="same_password_123")


def test_user_filter_dto_defaults():
    dto = UserFilterDTO()
    assert dto.search is None
    assert dto.is_active is None
    assert dto.is_deleted is None
    assert dto.limit == 50
    assert dto.offset == 0
