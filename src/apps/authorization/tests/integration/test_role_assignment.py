import pytest

from src.apps.authorization.exceptions.authorization_exceptions import (
    RoleAssignmentAlreadyExistsException,
)
from src.apps.authorization.models import Role
from src.apps.authorization.services.role_assignment_service import (
    RoleAssignmentService,
)
from src.apps.users.models import User


@pytest.mark.django_db
def test_assign_role_then_duplicate_assignment_fails():
    user = User.objects.create_user(email="test_assign_dup@test.com", password="password123")
    Role.objects.get_or_create(code="COORDINATOR", defaults={"name": "Coordinator", "pubkey": "role_coord_dup"})

    RoleAssignmentService.assign_role(user.pubkey, "COORDINATOR", assigned_by_pubkey=None)

    with pytest.raises(RoleAssignmentAlreadyExistsException):
        RoleAssignmentService.assign_role(user.pubkey, "COORDINATOR", assigned_by_pubkey=None)


@pytest.mark.django_db
def test_revoke_role_removes_assignment():
    user = User.objects.create_user(email="test_revoke_role@test.com", password="password123")
    Role.objects.get_or_create(code="COORDINATOR", defaults={"name": "Coordinator", "pubkey": "role_coord_rev"})

    RoleAssignmentService.assign_role(user.pubkey, "COORDINATOR", assigned_by_pubkey=None)
    RoleAssignmentService.revoke_role(user.pubkey, "COORDINATOR")

    roles = RoleAssignmentService.list_user_roles(user.pubkey)
    assert "COORDINATOR" not in [ur.role.code for ur in roles]
