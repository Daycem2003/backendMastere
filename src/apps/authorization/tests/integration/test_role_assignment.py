"""
Ces tests nécessitent une base Postgres de test réelle (pas de mock) car ils
valident les contraintes d'unicité (`@@unique([userId, roleId])`) et les
cascades définies au niveau du schéma Prisma, qu'un mock ne peut pas
reproduire fidèlement.

Pré-requis avant de lancer `pytest tests/integration` :
  1. Une base Postgres de test dédiée (jamais la base de dev), configurée via
     une variable DATABASE_URL_TEST séparée dans .env.test
  2. `poetry run prisma migrate deploy` appliqué sur cette base de test
  3. Un fixture pytest (à ajouter dans tests/conftest.py, pas encore créé)
     qui : (a) connecte `db` vers DATABASE_URL_TEST, (b) truncate les tables
     concernées avant/après chaque test pour l'isolation.

TODO(infra): créer backend/tests/conftest.py avec ce fixture avant d'activer
ces tests en CI. Ils sont volontairement marqués `skip` pour l'instant afin
de ne pas casser une CI qui n'a pas encore de base de test provisionnée.
"""

import pytest

from src.apps.authorization.services.role_assignment_service import RoleAssignmentService
from src.apps.authorization.exceptions.authorization_exceptions import (
    RoleAssignmentAlreadyExistsException,
)


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec une DB Postgres de test provisionnée")
@pytest.mark.asyncio
async def test_assign_role_then_duplicate_assignment_fails():
    # Arrange : un user CANDIDATE existant en base de test, et le rôle COORDINATOR seedé.
    user_pubkey = "usr_test_integration_001"
    role_code = "COORDINATOR"

    # Act
    await RoleAssignmentService.assign_role(user_pubkey, role_code, assigned_by_pubkey=None)

    # Assert : une deuxième assignation identique doit échouer proprement.
    with pytest.raises(RoleAssignmentAlreadyExistsException):
        await RoleAssignmentService.assign_role(user_pubkey, role_code, assigned_by_pubkey=None)


@pytest.mark.skip(reason="Nécessite tests/conftest.py avec une DB Postgres de test provisionnée")
@pytest.mark.asyncio
async def test_revoke_role_removes_permission():
    user_pubkey = "usr_test_integration_002"
    role_code = "COORDINATOR"

    await RoleAssignmentService.assign_role(user_pubkey, role_code, assigned_by_pubkey=None)
    await RoleAssignmentService.revoke_role(user_pubkey, role_code)

    roles = await RoleAssignmentService.list_user_roles(user_pubkey)
    assert role_code not in [ur.role.code for ur in roles]
