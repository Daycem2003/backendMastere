from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from src.apps.users.dto.user import CreateUserDTO
from src.apps.users.services.user_service import UserService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def candidate_user():
    return UserService.create_user(
        CreateUserDTO(email="candidate@test.com", password="password12345", role="CANDIDATE")
    )


@pytest.fixture
def admin_user():
    return UserService.create_user(
        CreateUserDTO(email="admin@test.com", password="password12345", role="ADMIN")
    )


@pytest.fixture
def other_user():
    return UserService.create_user(
        CreateUserDTO(email="other@test.com", password="password12345", role="CANDIDATE")
    )


@pytest.mark.django_db
def test_get_current_user_me(api_client, candidate_user):
    api_client.force_authenticate(user=candidate_user)
    response = api_client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.data["pubkey"] == candidate_user.pubkey
    assert response.data["email"] == candidate_user.email
    assert response.data["is_active"] is True


@pytest.mark.django_db
def test_patch_current_user_me(api_client, candidate_user):
    api_client.force_authenticate(user=candidate_user)
    response = api_client.patch("/api/v1/users/me", {"email": "new.email@test.com"}, format="json")

    assert response.status_code == 200
    assert response.data["email"] == "new.email@test.com"


@pytest.mark.django_db
def test_change_password_api(api_client, candidate_user):
    api_client.force_authenticate(user=candidate_user)
    response = api_client.post(
        "/api/v1/users/me/change-password",
        {"old_password": "password12345", "new_password": "brand_new_password_999"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["message"] == "Mot de passe modifié avec succès."


@pytest.mark.django_db
@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_list_users_as_admin(mock_has_role, api_client, admin_user, candidate_user):
    mock_has_role.side_effect = lambda pubkey, role: role == "ADMIN"
    api_client.force_authenticate(user=admin_user)

    response = api_client.get("/api/v1/users/")
    assert response.status_code == 200
    assert response.data["count"] >= 2
    assert len(response.data["results"]) >= 2


@pytest.mark.django_db
@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_list_users_as_candidate_forbidden(mock_has_role, api_client, candidate_user):
    mock_has_role.return_value = False
    api_client.force_authenticate(user=candidate_user)

    response = api_client.get("/api/v1/users/")
    assert response.status_code == 403


@pytest.mark.django_db
@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_get_user_detail_other_forbidden(mock_has_role, api_client, candidate_user, other_user):
    mock_has_role.return_value = False
    api_client.force_authenticate(user=candidate_user)

    response = api_client.get(f"/api/v1/users/{other_user.pubkey}")
    assert response.status_code == 403


@pytest.mark.django_db
@patch("src.apps.users.policies.user_policy.AuthorizationService.has_role")
def test_get_user_detail_as_admin(mock_has_role, api_client, admin_user, candidate_user):
    mock_has_role.side_effect = lambda pubkey, role: role == "ADMIN"
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(f"/api/v1/users/{candidate_user.pubkey}")
    assert response.status_code == 200
    assert response.data["pubkey"] == candidate_user.pubkey


@pytest.mark.django_db
@patch("src.apps.users.permissions.user_permissions.AuthorizationService.has_role")
def test_admin_deactivate_and_activate_user_api(mock_has_role, api_client, admin_user, candidate_user):
    mock_has_role.return_value = True
    api_client.force_authenticate(user=admin_user)

    # Deactivate
    resp_deact = api_client.post(f"/api/v1/users/{candidate_user.pubkey}/deactivate", {"reason": "Test"}, format="json")
    assert resp_deact.status_code == 200
    assert resp_deact.data["is_active"] is False

    # Activate
    resp_act = api_client.post(f"/api/v1/users/{candidate_user.pubkey}/activate")
    assert resp_act.status_code == 200
    assert resp_act.data["is_active"] is True


@pytest.mark.django_db
@patch("src.apps.users.permissions.user_permissions.AuthorizationService.has_role")
def test_admin_delete_and_restore_user_api(mock_has_role, api_client, admin_user, candidate_user):
    mock_has_role.return_value = True
    api_client.force_authenticate(user=admin_user)

    # Delete
    resp_del = api_client.delete(f"/api/v1/users/{candidate_user.pubkey}")
    assert resp_del.status_code == 200
    assert resp_del.data["is_deleted"] is True

    # Restore
    resp_res = api_client.post(f"/api/v1/users/{candidate_user.pubkey}/restore")
    assert resp_res.status_code == 200
    assert resp_res.data["is_deleted"] is False
    assert resp_res.data["is_active"] is True
