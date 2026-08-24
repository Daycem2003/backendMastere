"""Middleware ASGI qui authentifie la connexion websocket via le même JWT
que le reste de l'API REST (module `authentication`).

Le token est attendu en query string : wss://.../ws/notifications/?token=...
(les navigateurs ne permettent pas de header Authorization personnalisé sur
un handshake WebSocket natif).

ADAPTER `_decode_token` ci-dessous à la méthode exacte exposée par votre
`TokenService` (le nom peut différer légèrement selon la version du module
`authentication` — decode_access_token / verify_access_token / etc.).
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


def _decode_token(token: str) -> int | None:
    """Retourne le user_id encodé dans le token, ou None si invalide/expiré.

    À adapter à l'API réelle de TokenService du module `authentication` :
    ex. `TokenService.decode_access_token(token)` renvoyant un payload dict
    avec une clé `sub`/`user_id`.
    """
    from src.apps.authentication.services.token_service import TokenService

    try:
        payload = TokenService.decode_access_token(token)
        return payload.get("user_id") or payload.get("sub")
    except Exception:
        return None


@database_sync_to_async
def _get_user(user_id: int):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id, is_active=True)
        return user
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        scope["user"] = AnonymousUser()
        if token:
            user_id = _decode_token(token)
            if user_id is not None:
                scope["user"] = await _get_user(user_id)

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    from channels.sessions import CookieMiddleware

    return CookieMiddleware(JWTAuthMiddleware(inner))
