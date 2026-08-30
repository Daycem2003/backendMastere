from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.apps.authorization.exceptions.authorization_exceptions import (
    PermissionDeniedException,
)
from src.apps.authorization.permissions.permission_based import require_permission
from src.apps.authorization.permissions.role_based import require_roles
from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException


@pytest.mark.asyncio
@patch("src.apps.authorization.permissions.role_based.UserRole")
async def test_require_roles_allows_matching_role(mock_user_role):
    mock_user_role.objects.filter.return_value.exists.return_value = True
    dependency = require_roles("ADMIN")
    user = SimpleNamespace(pubkey="usr_admin_123")

    result = await dependency(current_user=user)

    assert result is user


@pytest.mark.asyncio
@patch("src.apps.authorization.permissions.role_based.UserRole")
async def test_require_roles_rejects_non_matching_role(mock_user_role):
    mock_user_role.objects.filter.return_value.exists.return_value = False
    dependency = require_roles("ADMIN")
    user = SimpleNamespace(pubkey="usr_candidate_123")

    with pytest.raises(InsufficientPermissionsException):
        await dependency(current_user=user)



@pytest.mark.asyncio
@patch("src.apps.authorization.permissions.permission_based.AuthorizationService")
async def test_require_permission_allows_when_granted(mock_service):
    mock_service.check_or_raise = AsyncMock(return_value=None)
    dependency = require_permission("master:create")
    user = SimpleNamespace(pubkey="usr_demo", role="COORDINATOR")

    result = await dependency(current_user=user)

    assert result is user


@pytest.mark.asyncio
@patch("src.apps.authorization.permissions.permission_based.AuthorizationService")
async def test_require_permission_denies_when_check_raises(mock_service):
    mock_service.check_or_raise = AsyncMock(side_effect=PermissionDeniedException("master:create"))
    dependency = require_permission("master:create")
    user = SimpleNamespace(pubkey="usr_demo", role="CANDIDATE")

    with pytest.raises(PermissionDeniedException):
        await dependency(current_user=user)
