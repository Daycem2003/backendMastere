from src.apps.applications.models import ApplicationStatus
from src.apps.authorization.services.authorization_service import AuthorizationService


class ApplicationPolicy:
    @staticmethod
    def can_view(user, application) -> bool:
        if application.candidate_profile.user_id == user.pk:
            return True
        if AuthorizationService.has_role(user.pubkey, "ADMIN"):
            return True
        return application.master.coordinateur.user_id == user.pk

    @staticmethod
    def can_withdraw(user, application) -> bool:
        if application.candidate_profile.user_id != user.pk:
            return False
        return application.statut in (ApplicationStatus.SOUMISE, ApplicationStatus.EN_COURS)

    @staticmethod
    def can_decide(user, application) -> bool:
        if application.statut not in (ApplicationStatus.SOUMISE, ApplicationStatus.EN_COURS):
            return False
        if AuthorizationService.has_role(user.pubkey, "ADMIN"):
            return True
        return application.master.coordinateur.user_id == user.pk
