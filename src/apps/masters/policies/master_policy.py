from src.apps.authorization.services.authorization_service import AuthorizationService
from src.apps.masters.models import MasterStatus


class MasterPolicy:
    @staticmethod
    def can_view(user, master) -> bool:
        """Un master OUVERT est visible publiquement (y compris anonyme,
        `user=None`) — un BROUILLON/FERME n'est visible que par son
        coordinateur ou un admin."""
        if master.statut == MasterStatus.OUVERT:
            return True
        if user is None or not user.is_authenticated:
            return False
        if AuthorizationService.has_role(user.pubkey, "ADMIN"):
            return True
        coordinateur = getattr(user, "coordinateur", None)
        return bool(coordinateur and master.coordinateur_id == coordinateur.id)

    @staticmethod
    def can_edit(user, master) -> bool:
        if AuthorizationService.has_role(user.pubkey, "ADMIN"):
            return True
        coordinateur = getattr(user, "coordinateur", None)
        return bool(coordinateur and master.coordinateur_id == coordinateur.id)

    @staticmethod
    def can_publish(user, master) -> bool:
        return MasterPolicy.can_edit(user, master)
