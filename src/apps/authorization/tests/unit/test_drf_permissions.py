from types import SimpleNamespace
from unittest.mock import patch

from src.apps.authorization.permissions.drf import require_permission


def test_has_permission_denies_anonymous_request():
    permission = require_permission("role:manage")()
    request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))

    assert permission.has_permission(request, SimpleNamespace()) is False


def test_has_permission_delegates_to_rbac_service():
    permission = require_permission("role:manage")()
    request = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True, pubkey="usr_admin")
    )

    with patch(
        "src.apps.authorization.permissions.drf.AuthorizationService.has_permission",
        return_value=True,
    ) as has_permission:
        assert permission.has_permission(request, SimpleNamespace()) is True

    has_permission.assert_called_once_with("usr_admin", "role:manage")
