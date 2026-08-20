from src.apps.authentication.services.authentication_service import AuthenticationService
from src.apps.users.models import User


class LocalStrategy:
    @staticmethod
    def authenticate(email: str, password: str) -> User:
        from src.apps.authentication.dto.login import LoginRequestDTO

        return AuthenticationService.login(LoginRequestDTO(email=email, password=password))
