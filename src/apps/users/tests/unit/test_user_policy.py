from types import SimpleNamespace
from unittest.mock import patch

from src.apps.users.policies.user_policy import UserPolicy


def _user(pk=1, pubkey="usr_1", is_authenticated=True):
    return SimpleNamespace(pk=pk, pubkey=pubkey, is_authenticated=is_authenticated)


def test_can_view_user_self():
    user = _user(pk=1, pubkey="usr_1")
    assert UserPolicy.can_view_user(user, user) is True


def test_can_view_user_unauthenticated():
    user = _user(pk=1, pubkey="usr_1", is_authenticated=False)
    target = _user(pk=2, pubkey="usr_2")
    assert UserPolicy.can_view_user(user, target) is False


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_view_user_admin(mock_has_role):
    admin = _user(pk=1, pubkey="usr_admin")
    target = _user(pk=2, pubkey="usr_target")

    mock_has_role.side_effect = lambda pubkey, role: role == "ADMIN"
    assert UserPolicy.can_view_user(admin, target) is True


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_view_user_other_regular_candidate(mock_has_role):
    user = _user(pk=1, pubkey="usr_candidate1")
    target = _user(pk=2, pubkey="usr_candidate2")

    mock_has_role.return_value = False
    assert UserPolicy.can_view_user(user, target) is False


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_list_users_coordinator(mock_has_role):
    coordinator = _user(pk=1, pubkey="usr_coord")
    mock_has_role.side_effect = lambda pubkey, role: role == "COORDINATOR"
    assert UserPolicy.can_list_users(coordinator) is True


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_list_users_candidate_denied(mock_has_role):
    candidate = _user(pk=1, pubkey="usr_cand")
    mock_has_role.return_value = False
    assert UserPolicy.can_list_users(candidate) is False


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_update_user_self(mock_has_role):
    user = _user(pk=1, pubkey="usr_1")
    assert UserPolicy.can_update_user(user, user) is True


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_update_user_admin(mock_has_role):
    admin = _user(pk=1, pubkey="usr_admin")
    target = _user(pk=2, pubkey="usr_target")
    mock_has_role.return_value = True
    assert UserPolicy.can_update_user(admin, target) is True


@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_can_manage_user_lifecycle_admin_only(mock_has_role):
    admin = _user(pk=1, pubkey="usr_admin")
    target = _user(pk=2, pubkey="usr_target")

    mock_has_role.return_value = True
    assert UserPolicy.can_manage_user_lifecycle(admin, target) is True

    mock_has_role.return_value = False
    assert UserPolicy.can_manage_user_lifecycle(admin, target) is False
