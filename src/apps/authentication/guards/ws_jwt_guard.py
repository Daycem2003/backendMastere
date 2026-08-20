from src.apps.authentication.strategies.ws_jwt_strategy import WsJwtStrategy


class WsJwtGuard:
    @staticmethod
    def authenticate(token: str):
        return WsJwtStrategy.authenticate(token)
