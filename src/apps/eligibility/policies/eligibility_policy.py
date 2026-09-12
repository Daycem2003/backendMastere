from src.apps.authorization.services.authorization_service import AuthorizationService


class EligibilityRulePolicy:
    @staticmethod
    def can_manage(user, master) -> bool:
        if AuthorizationService.has_role(user.pubkey, "ADMIN"):
            return True
        coordinateur = getattr(user, "coordinateur", None)
        return bool(coordinateur and master.coordinateur_id == coordinateur.id)
