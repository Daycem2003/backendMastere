from src.apps.authentication.services.password_service import PasswordService


def test_hash_password_returns_different_string_than_input():
    hashed = PasswordService.hash_password("MonMotDePasse123")
    assert hashed != "MonMotDePasse123"


def test_verify_password_succeeds_with_correct_password():
    hashed = PasswordService.hash_password("MonMotDePasse123")
    assert PasswordService.verify_password("MonMotDePasse123", hashed) is True


def test_verify_password_fails_with_wrong_password():
    hashed = PasswordService.hash_password("MonMotDePasse123")
    assert PasswordService.verify_password("MauvaisMotDePasse", hashed) is False
