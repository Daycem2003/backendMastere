import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Un socket par onglet ouvert ; tous les sockets d'un même utilisateur
    rejoignent le groupe `user:{user_id}` (voir emitter.notify_user)."""

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)  # non authentifié
            return

        self.group_name = f"user:{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("ws_connected", extra={"user_id": user.pk})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Canal descendant uniquement (serveur -> client) pour l'instant.
        # Un ping/pong applicatif simple est toléré pour garder la
        # connexion active derrière certains proxys.
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def notification_push(self, event):
        """Handler appelé par Channels pour tout message de group_send
        avec `"type": "notification.push"` (voir emitter.py)."""
        await self.send_json({"event": event["event"], "payload": event["payload"]})
