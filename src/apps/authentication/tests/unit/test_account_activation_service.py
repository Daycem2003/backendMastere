import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
from django.utils import timezone
from src.apps.authentication.services.account_activation_service import AccountActivationService
from src.shared.exceptions.auth_exceptions import InvalidTokenException


def test_create_activation_token():
    user = MagicMock(pk=1)
    with patch("src.apps.authentication.services.account_activation_service.AccountActivationToken.objects.filter") as mock_filter, \
         patch("src.apps.authentication.services.account_activation_service.AccountActivationToken.objects.create") as mock_create:
        mock_filter.return_value.delete.return_value = None
        mock_create.return_value = MagicMock(token="act_123")

        token_record = AccountActivationService.create_activation_token(user, ttl_hours=48)
        assert token_record.token == "act_123"
        mock_filter.assert_called_once_with(user=user, used_at__isnull=True)
        mock_create.assert_called_once()


def test_activate_account_success():
    user = MagicMock(pk=1, is_active=False)
    now = timezone.now()
    activation_record = MagicMock(
        user=user,
        expires_at=now + timedelta(hours=24),
        used_at=None,
    )

    with patch("src.apps.authentication.services.account_activation_service.AccountActivationToken.objects.select_related") as mock_sr, \
         patch("src.apps.authentication.services.account_activation_service.PasswordService.hash_password", return_value="hashed_secret"):
        mock_sr.return_value.filter.return_value.first.return_value = activation_record

        result_user = AccountActivationService.activate_account("valid_token", "MyNewPassword123")

        assert result_user == user
        assert user.password == "hashed_secret"
        assert user.is_active is True
        assert user.save.called
        assert activation_record.save.called


def test_activate_account_expired_or_invalid():
    with patch("src.apps.authentication.services.account_activation_service.AccountActivationToken.objects.select_related") as mock_sr:
        mock_sr.return_value.filter.return_value.first.return_value = None

        with pytest.raises(InvalidTokenException):
            AccountActivationService.activate_account("invalid_token", "MyNewPassword123")
