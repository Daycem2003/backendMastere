"""
Tests de l'autorité RBAC : la vérité est dans la table `UserRole`, il n'y a plus
de champ `role` sur l'utilisateur. Chaque scénario construit explicitement les
lignes `UserRole` (via `Role` / `UserRole`) plutôt que d'appuyer sur un champ
rôle obsolète qui n'existe plus.
"""

import pytest

from src.apps.authorization.models import Role, UserRole
from src.apps.authorization.permissions.drf import HasRole
from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.users.models import User


@pytest.fixture
def user_with_rbac_assignment():
    """Crée un utilisateur et lui assigne explicitement un rôle via la table RBAC."""
    user = User.objects.create_user(email="rbac_user@test.com", password="password123")
    coordinator_role, _ = Role.objects.get_or_create(
        code="COORDINATOR",
        defaults={"name": "Coordinateur", "pubkey": "role_coord_rbac_test"},
    )
    UserRole.objects.create(user=user, role=coordinator_role)
    return user


@pytest.mark.django_db
def test_user_with_rbac_assignment_is_authorized(user_with_rbac_assignment):
    """Un `UserRole` pointant vers le bon role suffit à autoriser l'utilisateur."""
    user = user_with_rbac_assignment

    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is True
    assert AuthorizationService.has_role(user.pubkey, "CANDIDATE") is False
    assert AuthorizationService.get_user_roles(user.pubkey) == ["COORDINATOR"]


@pytest.mark.django_db
def test_user_without_rbac_role_is_not_authorized():
    """Un utilisateur SANS aucune ligne `UserRole` n'est autorisé à rien : le
    service d'autorisation ne tient plus compte d'aucun champ rôle obsolète."""
    user = User.objects.create_user(email="no_rbac@test.com", password="password123")

    assert AuthorizationService.has_role(user.pubkey, "ADMIN") is False
    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is False
    assert AuthorizationService.has_permission(user.pubkey, "role:manage") is False


@pytest.mark.django_db
def test_non_rbac_fields_do_not_change_rbac_decision(user_with_rbac_assignment):
    """La décision RBAC ne dépend que de la ligne `UserRole` : muter un champ
    non-RBAC de l'utilisateur (`is_active`) n'altère pas le résultat."""
    user = user_with_rbac_assignment

    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is True
    assert AuthorizationService.has_role(user.pubkey, "CANDIDATE") is False

    # Muter un champ sans rapport avec le RBAC ne doit rien changer.
    user.is_active = False
    user.save(update_fields=["is_active"])

    assert AuthorizationService.has_role(user.pubkey, "COORDINATOR") is True
    assert AuthorizationService.has_role(user.pubkey, "CANDIDATE") is False


@pytest.mark.django_db
def test_drf_has_role_permission_evaluates_only_rbac():
    """La permission DRF `HasRole` ne regarde que le role RBAC de l'utilisateur."""
    user_with_rbac = User.objects.create_user(email="rbac_user@test.com", password="password123")
    user_without_rbac = User.objects.create_user(email="no_rbac_user@test.com", password="password123")

    admin_role, _ = Role.objects.get_or_create(
        code="ADMIN",
        defaults={"name": "Administrateur", "pubkey": "role_admin_perm_test"},
    )
    UserRole.objects.create(user=user_with_rbac, role=admin_role)

    perm = HasRole()
    perm.required_role = "ADMIN"

    class DummyRequest:
        def __init__(self, user):
            self.user = user

    assert perm.has_permission(DummyRequest(user_with_rbac), None) is True
    assert perm.has_permission(DummyRequest(user_without_rbac), None) is False
