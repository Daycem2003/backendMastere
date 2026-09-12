"""Tests ciblant l'exigence d'atomicité : création d'identité + assignation
du rôle initial doivent former une seule opération. Les assertions sur le
VRAI rollback transactionnel nécessitent une base de données réelle
(@pytest.mark.django_db) — je ne peux pas exécuter ces tests dans cet
environnement sans DB. Ils sont fournis, marqués explicitement, à lancer
avec `poetry run pytest src/apps/users -v` de ton côté.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.apps.users.dto.user import CreateUserIdentityDTO
from src.apps.users.services.user_provisioning_service import UserProvisioningService


@pytest.mark.django_db
@patch("src.apps.authorization.services.role_assignment_service.RoleAssignmentService")
@patch("src.apps.users.services.user_provisioning_service.UserService")
def test_create_user_with_role_calls_both_steps_in_order(mock_user_service, mock_role_service):
    created_user = MagicMock(pk=1)
    mock_user_service.create_identity.return_value = created_user

    result = UserProvisioningService.create_user_with_role(
        CreateUserIdentityDTO(email="x@example.com", password_hash="h"),
        role_code="CANDIDATE",
        assigned_by=None,
    )

    mock_user_service.create_identity.assert_called_once()
    mock_role_service.assign_role.assert_called_once_with(
        created_user, "CANDIDATE", assigned_by=None
    )
    assert result is created_user


@pytest.mark.django_db
def test_create_user_with_role_rolls_back_identity_if_role_assignment_fails():
    """⚠️ Nécessite une vraie base (django_db) — non exécutable ici.

    Doit vérifier : si `RoleAssignmentService.assign_role` lève une
    exception, le `User` créé par `UserService.create_identity` ne doit
    PAS persister en base (rollback de la transaction atomique portée par
    `UserProvisioningService.create_user_with_role`).
    """
    from src.apps.users.models import User

    with patch(
        "src.apps.authorization.services.role_assignment_service.RoleAssignmentService.assign_role",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError):
            UserProvisioningService.create_user_with_role(
                CreateUserIdentityDTO(email="rollback@example.com", password_hash="h"),
                role_code="CANDIDATE",
            )

    assert not User.objects.filter(email="rollback@example.com").exists()
