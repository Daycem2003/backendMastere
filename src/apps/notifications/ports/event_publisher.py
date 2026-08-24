from typing import Protocol


class EventPublisherProtocol(Protocol):
    """Port abstrait pour la publication d'événements de notification."""

    def publish(self, user_id: int, event: str, payload: dict) -> bool:
        """Publie un événement vers un utilisateur identifié."""
        ...
