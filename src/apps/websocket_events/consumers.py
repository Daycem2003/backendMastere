import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


@database_sync_to_async
def _get_user_groups(user):
    groups = [f"user:{user.pk}", "broadcast:all"]
    try:
        from src.apps.authorization.models.user_role import UserRole

        ur = UserRole.objects.filter(user=user).select_related("role").first()
        if ur and ur.role and ur.role.code:
            code = ur.role.code.upper()
            groups.append(f"role:{code}")
            if "COORD" in code:
                groups.extend(["role:COORDINATEURS", "role:COORDINATOR", "role:coordinateur"])
            elif "CAND" in code:
                groups.extend(["role:CANDIDATS", "role:CANDIDATE", "role:candidat"])
            elif "ADMIN" in code:
                groups.extend(["role:ADMIN", "role:ADMINISTRATEUR", "role:administrateur"])
    except Exception:
        pass
    return list(set(groups))


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Un socket par onglet ouvert ; tous les sockets d'un même utilisateur
    rejoignent le groupe `user:{user_id}` (voir emitter.notify_user)."""

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)  # non authentifié
            return

        self.groups_joined = await _get_user_groups(user)
        for grp in self.groups_joined:
            await self.channel_layer.group_add(grp, self.channel_name)

        await self.accept()
        logger.info("ws_connected", extra={"user_id": user.pk, "groups": self.groups_joined})

    async def disconnect(self, close_code):
        if hasattr(self, "groups_joined"):
            for grp in self.groups_joined:
                await self.channel_layer.group_discard(grp, self.channel_name)


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
