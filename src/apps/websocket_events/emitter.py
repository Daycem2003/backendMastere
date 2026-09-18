"""Point d'entrée unique pour émettre un événement temps réel vers un
utilisateur donné, depuis n'importe quel service Django (synchrone).

Usage :
    from src.apps.websocket_events.emitter import notify_user

    notify_user(
        user_id=42,
        event="notification:new",
        payload={"objet": "...", "corps": "..."},
    )

Le message arrive côté client connecté sur le group `user:{user_id}` (voir
consumers.py) sous la forme :
    {"event": "notification:new", "payload": {...}}
"""
import logging
import re

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

# Un nom de groupe Channels ne doit contenir que [A-Za-z0-9_.-] (< 100 chars).
# Les noms de ce systeme (ex: "user:1", "broadcast:all", "role:COORDINATEURS")
# portent des " : " interdits -> on les normalise a la barre basse UNIQUE,
# appliquee aux deux bords (emitter ET consumer) pour qu'ils se correspondent.
_INVALID_GROUP_CHARS = re.compile(r"[^A-Za-z0-9_.-]")


def sanitize_group_name(name: str) -> str:
    """Rend un nom de groupe conforme a Channels (barres basses pour tout
    caractere interdit). Identique aux deux bords : le producteur et
    le consommateur obtiennent le meme nom final."""
    return _INVALID_GROUP_CHARS.sub("_", name)


def _group_name(user_id: int) -> str:
    return f"user:{user_id}"


def notify_user(user_id: int, event: str, payload: dict) -> bool:
    """Émet un événement vers tous les sockets ouverts d'un utilisateur.

    Retourne False (sans lever d'exception) si aucun channel layer n'est
    configuré ou si l'envoi échoue — un échec d'émission temps réel ne doit
    jamais faire échouer l'opération métier qui l'a déclenché (le
    NotificationRecord, lui, est déjà persisté en base à ce stade).
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("websocket_channel_layer_not_configured", extra={"event": event})
        return False

    try:
        async_to_sync(channel_layer.group_send)(
            sanitize_group_name(_group_name(user_id)),
            {"type": "notification.push", "event": event, "payload": payload},
        )
        return True
    except Exception:
        logger.exception("websocket_emit_failed", extra={"user_id": user_id, "event": event})
        return False


def notify_group(group_name: str, event: str, payload: dict) -> bool:
    """Émet vers un groupe arbitraire (ex: `master:{master_id}` pour
    diffuser à tous les coordinateurs d'un master), pour usages futurs."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("websocket_channel_layer_not_configured", extra={"event": event})
        return False
    try:
        async_to_sync(channel_layer.group_send)(
            sanitize_group_name(group_name), {"type": "notification.push", "event": event, "payload": payload}
        )
        return True
    except Exception:
        logger.exception("websocket_emit_failed", extra={"group": group_name, "event": event})
        return False
