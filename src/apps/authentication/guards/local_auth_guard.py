from src.apps.authentication.strategies.local_strategy import LocalStrategy


class LocalAuthGuard:
    @staticmethod
    def authenticate(email: str, password: str):
        return LocalStrategy.authenticate(email, password)
