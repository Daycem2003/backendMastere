from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.apps.websocket_events.middleware import (
    AnonymousUser,
    JWTAuthMiddleware,
    _decode_token,
    _get_user,
)


def test_decode_token_with_valid_token():
    fake_token_service = MagicMock()
    fake_token_service.decode_and_require_type.return_value = {
        "sub": "usr_test123",
        "role": "CANDIDATE",
        "type": "access",
    }

    result = _decode_token("valid_token", token_service=fake_token_service)
    assert result == "usr_test123"
    fake_token_service.decode_and_require_type.assert_called_once_with("valid_token", "access")


def test_decode_token_with_invalid_token_returns_none():
    fake_token_service = MagicMock()
    fake_token_service.decode_and_require_type.side_effect = Exception("Invalid token")

    result = _decode_token("invalid_token", token_service=fake_token_service)
    assert result is None


@pytest.mark.asyncio
async def test_get_user_returns_user_when_found():
    fake_user = SimpleNamespace(pubkey="usr_123", is_active=True, pk=10)
    with patch("src.apps.users.models.User.objects") as mock_user_objects:
        mock_user_objects.filter.return_value.first.return_value = fake_user
        user = await _get_user("usr_123")
        assert user == fake_user


@pytest.mark.asyncio
async def test_get_user_returns_anonymous_when_not_found():
    with patch("src.apps.users.models.User.objects") as mock_user_objects:
        mock_user_objects.filter.return_value.first.return_value = None
        user = await _get_user("usr_unknown")
        assert isinstance(user, AnonymousUser)


@pytest.mark.asyncio
async def test_jwt_auth_middleware_populates_scope_with_authenticated_user():
    fake_user = SimpleNamespace(pubkey="usr_abc", is_active=True, pk=5)
    inner_app = AsyncMock()
    middleware = JWTAuthMiddleware(inner_app)

    scope = {
        "type": "websocket",
        "query_string": b"token=test_valid_jwt",
    }

    with patch(
        "src.apps.websocket_events.middleware._decode_token", return_value="usr_abc"
    ), patch(
        "src.apps.websocket_events.middleware._get_user", new=AsyncMock(return_value=fake_user)
    ):
        await middleware(scope, AsyncMock(), AsyncMock())

    assert scope["user"] == fake_user
    inner_app.assert_called_once()


@pytest.mark.asyncio
async def test_jwt_auth_middleware_sets_anonymous_when_no_token():
    inner_app = AsyncMock()
    middleware = JWTAuthMiddleware(inner_app)

    scope = {
        "type": "websocket",
        "query_string": b"",
    }

    await middleware(scope, AsyncMock(), AsyncMock())

    assert isinstance(scope["user"], AnonymousUser)
    inner_app.assert_called_once()
