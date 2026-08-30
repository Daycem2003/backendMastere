from unittest.mock import AsyncMock, patch

import pytest

from src.apps.authorization.exceptions.authorization_exceptions import (
    CannotModifySystemRoleException,
    RoleAlreadyExistsException,
)
from src.apps.authorization.services.role_service import RoleService


@pytest.mark.asyncio
@patch("src.apps.authorization.services.role_service.role_selector")
async def test_create_custom_role_fails_if_code_exists(mock_selector):
    mock_selector.get_role_by_code = AsyncMock(return_value=object())

    with pytest.raises(RoleAlreadyExistsException):
        await RoleService.create_custom_role("COORDINATOR", "Doublon", None)


@pytest.mark.asyncio
@patch("src.apps.authorization.services.role_service.role_selector")
async def test_delete_system_role_is_forbidden(mock_selector):
    fake_role = AsyncMock()
    fake_role.isSystem = True
    mock_selector.get_role_by_pubkey = AsyncMock(return_value=fake_role)

    with pytest.raises(CannotModifySystemRoleException):
        await RoleService.delete_role("role_system_admin")
