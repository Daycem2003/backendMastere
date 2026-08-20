from rest_framework import authentication, exceptions

from src.apps.authentication.strategies.jwt_strategy import JwtStrategy
from src.apps.users.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].decode().lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Invalid authorization header.")
        try:
            payload = JwtStrategy.validate_access_token(header[1].decode())
        except Exception as error:
            raise exceptions.AuthenticationFailed("Invalid access token.") from error
        user = User.objects.filter(pubkey=payload["sub"], is_active=True).first()
        if not user:
            raise exceptions.AuthenticationFailed("User not found or inactive.")
        return user, None
