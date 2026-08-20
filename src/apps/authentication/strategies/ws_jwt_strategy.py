from src.apps.authentication.models import UserModel
from src.apps.authentication.strategies.jwt_strategy import JwtStrategy
from src.apps.users.models import User


class WsJwtStrategy:
    @staticmethod
    def authenticate(token: str) -> UserModel:
        payload = JwtStrategy.validate_access_token(token)
        user = User.objects.filter(pubkey=payload["sub"], is_active=True).first()
        return user
