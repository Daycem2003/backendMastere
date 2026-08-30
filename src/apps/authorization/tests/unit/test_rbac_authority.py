import pytest

from src.apps.authorization.models import Role, UserRole
from src.apps.authorization.permissions.drf import HasRole
from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.users.models import User
from src.apps.users.models import UserRole as LegacyUserRole


@pytest.mark.django_db
def test_user_with_rbac_assignment_is_authorized():
    user = User.objects.create_user(email="authorized_admin@test.com", password="password123")
    admin_role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"name": "Admin", "pubkey": "role_admin_test"})
    UserRole.objects.create(user=user, role=admin_role)

    assert AuthorizationService.has_role(user.pubkey, "ADMIN") is True


@pytest.mark.django_db
def test_user_with_only_legacy_role_is_not_authorized():
    # User has legacy column set to ADMIN, but NO row in AUTH_USER_ROLES
    user = User.objects.create_user(
        email="fake_admin@test.com",
        password="password123",
        role=LegacyUserRole.ADMIN,
    )

    # RBAC check must evaluate to FALSE
    assert AuthorizationService.has_role(user.pubkey, "ADMIN") is False
    assert AuthorizationService.has_permission(user.pubkey, "role:manage") is False


@pytest.mark.django_db
def test_altering_legacy_role_column_does_not_change_rbac_decision():
    user = User.objects.create_user(email="regular_user@test.com", password="password123")
    coordinator_role, _ = Role.objects.get_or_create(
        code="COORDINATOR", defaults={"name": "Coordinator", "pubkey": "role_coord_test"}
    )
    UserRole.objects.create(user=user, role=coordinator_role)

    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is True

    # Mutate legacy column to CANDIDATE
    user.role = LegacyUserRole.CANDIDATE
    user.save(update_fields=["role"])

    # RBAC authority remains untouched
    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is True
    assert AuthorizationService.has_role(user.pubkey, "CANDIDATE") is False


@pytest.mark.django_db
def test_drf_has_role_permission_evaluates_only_rbac():
    user_with_rbac = User.objects.create_user(email="rbac_user@test.com", password="password123")
    user_without_rbac = User.objects.create_user(
        email="legacy_user@test.com", password="password123", role=LegacyUserRole.ADMIN
    )

    admin_role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"name": "Admin", "pubkey": "role_admin_perm_test"})
    UserRole.objects.create(user=user_with_rbac, role=admin_role)

    perm = HasRole()
    perm.required_role = "ADMIN"

    class DummyRequest:
        def __init__(self, u):
            self.user = u

    assert perm.has_permission(DummyRequest(user_with_rbac), None) is True
    assert perm.has_permission(DummyRequest(user_without_rbac), None) is False
