"""Middleware ASGI qui authentifie la connexion websocket via le même JWT
que le reste de l'API REST (module `authentication`).

Le token est attendu en query string : wss://.../ws/notifications/?token=...
(les navigateurs ne permettent pas de header Authorization personnalisé sur
un handshake WebSocket natif).
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from src.apps.websocket_events.protocols import TokenDecoderProtocol

logger = logging.getLogger(__name__)


def _decode_token(token: str, token_service: TokenDecoderProtocol | None = None) -> str | None:
    """Retourne le pubkey utilisateur encodé dans le claim `sub`, ou None si invalide/expiré."""
    if token_service is None:
        from src.apps.authentication.services.token_service import TokenService
        token_service = TokenService

    try:
        payload = token_service.decode_and_require_type(token, "access")
        return payload.get("sub")
    except Exception:
        return None


@database_sync_to_async
def _get_user(user_pubkey: str):
    """Récupère l'utilisateur actif via son pubkey dans le modèle User du projet (table MST_USERS)."""
    from src.apps.users.models import User

    try:
        user = User.objects.filter(pubkey=user_pubkey, is_active=True).first()
        return user if user is not None else AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        scope["user"] = AnonymousUser()
        if token:
            user_pubkey = _decode_token(token)
            if user_pubkey is not None:
                scope["user"] = await _get_user(user_pubkey)

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    from channels.sessions import CookieMiddleware

    return CookieMiddleware(JWTAuthMiddleware(inner))
