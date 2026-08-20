from src.apps.authentication.strategies.jwt_refresh_token_strategy import JwtRefreshTokenStrategy


class JwtRefreshTokenGuard:
    @staticmethod
    def validate(token: str):
        return JwtRefreshTokenStrategy.validate(token)
