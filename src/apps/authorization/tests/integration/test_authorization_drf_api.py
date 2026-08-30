import pytest
from rest_framework.test import APIClient

from src.apps.authorization.models import Role, UserRole
from src.apps.authorization.services.permission_service import PermissionService
from src.apps.authorization.services.role_service import RoleService
from src.apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(email="rbac_admin@test.com", password="password123")
    PermissionService._seed_default_permissions()
    RoleService._seed_default_roles()
    admin_role = Role.objects.get(code="ADMIN")
    UserRole.objects.create(user=user, role=admin_role)
    return user


@pytest.fixture
def regular_user():
    user = User.objects.create_user(email="rbac_regular@test.com", password="password123")
    return user


@pytest.mark.django_db
def test_list_permissions_api(api_client, admin_user, regular_user):
    # Anonymous -> 403
    resp_anon = api_client.get("/api/v1/authorization/permissions")
    assert resp_anon.status_code in (401, 403)

    # Regular user (no permission:manage) -> 403
    api_client.force_authenticate(user=regular_user)
    resp_forbidden = api_client.get("/api/v1/authorization/permissions")
    assert resp_forbidden.status_code == 403

    # Admin user -> 200
    api_client.force_authenticate(user=admin_user)
    resp_admin = api_client.get("/api/v1/authorization/permissions")
    assert resp_admin.status_code == 200
    assert len(resp_admin.data) > 0


@pytest.mark.django_db
def test_roles_crud_drf_api(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    # 1. List roles
    resp_list = api_client.get("/api/v1/authorization/roles")
    assert resp_list.status_code == 200
    codes = [r["code"] for r in resp_list.data]
    assert "ADMIN" in codes
    assert "COORDINATOR" in codes
    assert "CANDIDATE" in codes

    # 2. Create custom role
    create_payload = {
        "code": "AUDITOR",
        "name": "Auditeur Qualité",
        "description": "Rôle pour auditer les dossiers",
    }
    resp_create = api_client.post(
        "/api/v1/authorization/roles", create_payload, format="json"
    )
    assert resp_create.status_code == 201
    role_pubkey = resp_create.data["pubkey"]
    assert resp_create.data["code"] == "AUDITOR"

    # 3. Get role detail
    resp_get = api_client.get(f"/api/v1/authorization/roles/{role_pubkey}")
    assert resp_get.status_code == 200
    assert resp_get.data["name"] == "Auditeur Qualité"

    # 4. Patch role
    patch_payload = {"name": "Auditeur Principal"}
    resp_patch = api_client.patch(
        f"/api/v1/authorization/roles/{role_pubkey}", patch_payload, format="json"
    )
    assert resp_patch.status_code == 200
    assert resp_patch.data["name"] == "Auditeur Principal"

    # 5. Assign permission to role
    resp_perm_assign = api_client.post(
        f"/api/v1/authorization/roles/{role_pubkey}/permissions/application:view_all"
    )
    assert resp_perm_assign.status_code == 200
    assigned_perm_codes = [p["code"] for p in resp_perm_assign.data["permissions"]]
    assert "application:view_all" in assigned_perm_codes

    # 6. Revoke permission from role
    resp_perm_revoke = api_client.delete(
        f"/api/v1/authorization/roles/{role_pubkey}/permissions/application:view_all"
    )
    assert resp_perm_revoke.status_code == 200
    remaining_perm_codes = [p["code"] for p in resp_perm_revoke.data["permissions"]]
    assert "application:view_all" not in remaining_perm_codes

    # 7. Delete custom role
    resp_delete = api_client.delete(f"/api/v1/authorization/roles/{role_pubkey}")
    assert resp_delete.status_code == 204


@pytest.mark.django_db
def test_user_role_assignment_drf_api(api_client, admin_user, regular_user):
    api_client.force_authenticate(user=admin_user)

    # 1. Assign COORDINATOR role to regular user
    assign_payload = {
        "user_pubkey": regular_user.pubkey,
        "role_code": "COORDINATOR",
    }
    resp_assign = api_client.post(
        "/api/v1/authorization/users/roles", assign_payload, format="json"
    )
    assert resp_assign.status_code == 201
    assert resp_assign.data["role_code"] == "COORDINATOR"

    # 2. List roles assigned to user
    resp_list_user_roles = api_client.get(
        f"/api/v1/authorization/users/{regular_user.pubkey}/roles"
    )
    assert resp_list_user_roles.status_code == 200
    user_role_codes = [r["code"] for r in resp_list_user_roles.data]
    assert "COORDINATOR" in user_role_codes

    # 3. Revoke COORDINATOR role from user
    resp_revoke = api_client.delete(
        f"/api/v1/authorization/users/{regular_user.pubkey}/roles/COORDINATOR"
    )
    assert resp_revoke.status_code == 204

    # 4. Verify role is revoked
    resp_list_after = api_client.get(
        f"/api/v1/authorization/users/{regular_user.pubkey}/roles"
    )
    assert resp_list_after.status_code == 200
    assert "COORDINATOR" not in [r["code"] for r in resp_list_after.data]
