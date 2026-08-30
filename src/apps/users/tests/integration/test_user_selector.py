import pytest

from src.apps.users.dto.user import CreateUserDTO, UserFilterDTO
from src.apps.users.selectors.user_selector import (
    count_users,
    get_active_user_by_email,
    get_active_user_by_pubkey,
    get_user_by_email,
    get_user_by_id,
    get_user_by_pubkey,
    list_users,
)
from src.apps.users.services.user_lifecycle_service import UserLifecycleService
from src.apps.users.services.user_service import UserService


@pytest.mark.django_db
def test_user_selectors_lookup():
    user = UserService.create_user(CreateUserDTO(email="selector.test@example.com", password="password12345"))

    assert get_user_by_id(user.id) == user
    assert get_user_by_pubkey(user.pubkey) == user
    assert get_user_by_email("SELECTOR.TEST@example.com") == user
    assert get_active_user_by_pubkey(user.pubkey) == user
    assert get_active_user_by_email("selector.test@example.com") == user


@pytest.mark.django_db
def test_user_selectors_deleted_filtering():
    user = UserService.create_user(CreateUserDTO(email="deleted.selector@example.com", password="password12345"))
    admin = UserService.create_user(CreateUserDTO(email="admin.selector@example.com", password="password12345"))

    UserLifecycleService.soft_delete_user(user.pubkey, actor=admin)

    # By default, should not return deleted user
    assert get_user_by_pubkey(user.pubkey) is None
    assert get_user_by_email(user.email) is None
    assert get_active_user_by_pubkey(user.pubkey) is None

    # With include_deleted=True
    assert get_user_by_pubkey(user.pubkey, include_deleted=True) == user
    assert get_user_by_email(user.email, include_deleted=True) == user


@pytest.mark.django_db
def test_list_users_filtering_and_count():
    u1 = UserService.create_user(CreateUserDTO(email="alpha@test.com", password="password12345"))
    u2 = UserService.create_user(CreateUserDTO(email="beta@test.com", password="password12345"))
    admin = UserService.create_user(CreateUserDTO(email="gamma.admin@test.com", password="password12345"))

    UserLifecycleService.deactivate_user(u2.pubkey, actor=admin)

    # Active filter
    active_users = list(list_users(UserFilterDTO(is_active=True)))
    assert u1 in active_users
    assert u2 not in active_users

    # Search filter
    search_results = list(list_users(UserFilterDTO(search="alpha")))
    assert search_results == [u1]

    # Count
    assert count_users(UserFilterDTO(search="alpha")) == 1
