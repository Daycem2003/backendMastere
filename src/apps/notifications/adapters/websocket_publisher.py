import logging

from src.apps.notifications.ports.event_publisher import EventPublisherProtocol

logger = logging.getLogger(__name__)


class WebsocketEventPublisher(EventPublisherProtocol):
    """Adaptateur concret publiant les notifications via le module websocket_events."""

    def publish(self, user_id: int, event: str, payload: dict) -> bool:
        try:
            from src.apps.websocket_events.emitter import notify_user

            return notify_user(user_id=user_id, event=event, payload=payload)
        except Exception:
            logger.exception(
                "websocket_publish_failed",
                extra={"user_id": user_id, "event": event},
            )
            return False
