import pytest

from src.apps.authentication.services.token_service import TokenService
from src.shared.exceptions.auth_exceptions import InvalidTokenException


def test_access_token_can_be_decoded():
    token = TokenService.create_access_token(subject="usr_demo123", role="CANDIDATE")
    payload = TokenService.decode(token)

    assert payload["sub"] == "usr_demo123"
    assert payload["role"] == "CANDIDATE"
    assert payload["type"] == "access"


def test_refresh_token_produces_new_valid_pair():
    refresh_token = TokenService.create_refresh_token(subject="usr_demo123", role="CANDIDATE")
    new_pair = TokenService.refresh_access_token(refresh_token)

    decoded_access = TokenService.decode(new_pair.access_token)
    assert decoded_access["sub"] == "usr_demo123"
    assert decoded_access["type"] == "access"


def test_decode_invalid_token_raises_exception():
    with pytest.raises(InvalidTokenException):
        TokenService.decode("token.invalide.corrompu")


def test_access_token_rejected_as_refresh_type():
    access_token = TokenService.create_access_token(subject="usr_demo123", role="CANDIDATE")

    with pytest.raises(InvalidTokenException):
        TokenService.decode_and_require_type(access_token, "refresh")
