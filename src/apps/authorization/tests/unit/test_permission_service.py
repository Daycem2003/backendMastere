from unittest.mock import AsyncMock, patch

import pytest

from src.apps.authorization.exceptions.authorization_exceptions import (
    PermissionNotFoundException,
)
from src.apps.authorization.services.permission_service import PermissionService


@pytest.mark.asyncio
@patch("src.apps.authorization.services.permission_service.permission_selector")
async def test_get_permission_raises_when_missing(mock_selector):
    mock_selector.get_permission_by_code = AsyncMock(return_value=None)

    with pytest.raises(PermissionNotFoundException):
        await PermissionService.get_permission("inexistant:code")


@pytest.mark.asyncio
@patch("src.apps.authorization.services.permission_service.permission_selector")
async def test_get_permission_returns_it_when_found(mock_selector):
    fake_permission = AsyncMock()
    mock_selector.get_permission_by_code = AsyncMock(return_value=fake_permission)

    result = await PermissionService.get_permission("master:create")

    assert result is fake_permission
