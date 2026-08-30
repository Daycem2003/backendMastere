from unittest.mock import patch

import pytest

from src.apps.authorization.services.authorization_service import AuthorizationService


@pytest.mark.asyncio
@patch("src.apps.authorization.services.authorization_service.get_effective_permission_codes")
async def test_user_has_permission_true(mock_get_codes):
    mock_get_codes.return_value = {"master:create", "master:update"}

    result = await AuthorizationService.user_has_permission("usr_demo", "master:create")

    assert result is True


@pytest.mark.asyncio
@patch("src.apps.authorization.services.authorization_service.get_effective_permission_codes")
async def test_user_has_permission_false(mock_get_codes):
    mock_get_codes.return_value = {"master:update"}

    result = await AuthorizationService.user_has_permission("usr_demo", "master:create")

    assert result is False


@pytest.mark.asyncio
@patch("src.apps.authorization.services.authorization_service.get_effective_permission_codes")
async def test_check_or_raise_raises_when_missing(mock_get_codes):
    from src.apps.authorization.exceptions.authorization_exceptions import (
        PermissionDeniedException,
    )

    mock_get_codes.return_value = set()

    with pytest.raises(PermissionDeniedException):
        await AuthorizationService.check_or_raise("usr_demo", "master:create")


@pytest.mark.asyncio
@patch("src.apps.authorization.services.authorization_service.get_effective_permission_codes")
async def test_user_has_all_permissions(mock_get_codes):
    mock_get_codes.return_value = {"master:create", "master:update", "master:delete"}

    result = await AuthorizationService.user_has_all_permissions(
        "usr_demo", ["master:create", "master:update"]
    )

    assert result is True
