import pytest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from src.apps.authorization.permissions.role_based import require_roles
from src.apps.authorization.permissions.permission_based import require_permission
from src.shared.exceptions.auth_exceptions import InsufficientPermissionsException
from src.apps.authorization.exceptions.authorization_exceptions import PermissionDeniedException


@pytest.mark.asyncio
async def test_require_roles_allows_matching_role():
    dependency = require_roles("ADMIN")
    user = SimpleNamespace(role="ADMIN")

    result = await dependency(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_require_roles_rejects_non_matching_role():
    dependency = require_roles("ADMIN")
    user = SimpleNamespace(role="CANDIDATE")

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
