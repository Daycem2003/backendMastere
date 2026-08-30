import logging
import uuid

from django.db import transaction

from src.apps.applications.dto.application import DecisionDTO, SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import (
    AlreadyApplied,
    ApplicationAlreadyDecided,
    ApplicationNotWithdrawable,
    MasterNotFound,
    MasterNotOpen,
    MissingRequiredDocuments,
    NotEligible,
)
from src.apps.applications.models import Application, ApplicationStatus
from src.apps.applications.selectors.application_selector import get_active_for_candidate_and_master
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.candidate_profile.services.eligibility_service import EligibilityService
from src.apps.documents.selectors.document_selector import candidate_has_approved_type
from src.apps.notifications.dto.notification import NotifyDocumentIssueDTO
from src.apps.notifications.models import NotificationMotif
from src.apps.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ApplicationService:
    @staticmethod
    def _resolve_niveau(profile: CandidateProfile, master) -> str:
        """Détermine à quel niveau le candidat postule, en réutilisant
        `EligibilityService` (module `candidate_profile`) plutôt qu'en
        dupliquant la logique d'éligibilité ici :

        - éligible via le diplôme de licence -> candidature classique "M1".
        - pas de diplôme éligible mais un Master1Year validé (passerelle,
          y compris via un M1 fait hors plateforme, à valider manuellement
          par un coordinateur) -> candidature "M2".
        """
        if EligibilityService.is_eligible_via_licence(profile, master):
            return "M1"
        if EligibilityService.is_eligible_via_passerelle(profile, master) or (
            EligibilityService.requires_manual_review(profile)
        ):
            return "M2"
        raise NotEligible()

    @staticmethod
    @transaction.atomic
    def submit(profile: CandidateProfile, dto: SubmitApplicationDTO) -> Application:
        from src.apps.masters.models import Master, MasterStatus  # import tardif, évite le couplage au chargement

        master = Master.objects.select_for_update().filter(
            pubkey=dto.master_pubkey, deleted_at__isnull=True
        ).first()
        if not master:
            raise MasterNotFound()
        if master.statut != MasterStatus.OUVERT:
            raise MasterNotOpen()
        if get_active_for_candidate_and_master(profile.id, master.id):
            raise AlreadyApplied()

        niveau = ApplicationService._resolve_niveau(profile, master)

        required_types = list(
            master.required_documents.filter(deleted_at__isnull=True).values_list("type", flat=True)
        )
        missing = [
            t for t in required_types if not candidate_has_approved_type(profile.id, t)
        ]
        if missing:
            raise MissingRequiredDocuments(missing_types=missing)

        application = Application.objects.create(
            pubkey=f"app_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            master=master,
            niveau=niveau,
        )

        NotificationService.notify_document_issue(
            NotifyDocumentIssueDTO(
                candidate_profile_pubkey=profile.pubkey,
                application_pubkey=application.pubkey,
                motif=NotificationMotif.CANDIDATURE_STATUT,
                document_concerne=None,
                objet=f"Candidature soumise : {master.nom}",
                corps=f"Votre candidature ({niveau}) pour {master.nom} a été soumise avec succès.",
            ),
            actor=profile.user,
        )

        logger.info(
            "application_submitted",
            extra={"application_id": application.pk, "candidate_profile_id": profile.id, "master_id": master.id},
        )
        return application

    @staticmethod
    def withdraw(application: Application) -> None:
        """Aucun statut `RETIREE` n'existe dans le schéma
        (`ApplicationStatusEnum` ne couvre que SOUMISE/EN_COURS/ACCEPTEE/
        REJETEE) — le retrait est donc modélisé par un soft-delete, cohérent
        avec `deletedAt` déjà présent sur `Application`."""
        from django.utils import timezone

        if application.statut not in (ApplicationStatus.SOUMISE, ApplicationStatus.EN_COURS):
            raise ApplicationNotWithdrawable()
        application.deleted_at = timezone.now()
        application.save(update_fields=["deleted_at"])

    @staticmethod
    @transaction.atomic
    def decide(application: Application, dto: DecisionDTO, reviewer) -> Application:
        """NOTE : le schéma `Application` n'a pas de champ `reviewerId`/
        `reviewedAt` (contrairement à `DocumentVersion`) — la décision
        n'est donc pas tracée nommément sur l'objet lui-même ; seul le
        `NotificationRecord` généré ci-dessous et les logs applicatifs
        conservent une trace de qui a décidé et quand."""
        if application.statut not in (ApplicationStatus.SOUMISE, ApplicationStatus.EN_COURS):
            raise ApplicationAlreadyDecided()

        application.statut = ApplicationStatus.ACCEPTEE if dto.accept else ApplicationStatus.REJETEE
        application.save(update_fields=["statut"])

        objet = (
            f"Candidature acceptée : {application.master.nom}"
            if dto.accept
            else f"Candidature rejetée : {application.master.nom}"
        )
        corps = dto.motif or (
            "Félicitations, votre candidature a été acceptée."
            if dto.accept
            else "Votre candidature n'a malheureusement pas été retenue."
        )
        NotificationService.notify_document_issue(
            NotifyDocumentIssueDTO(
                candidate_profile_pubkey=application.candidate_profile.pubkey,
                application_pubkey=application.pubkey,
                motif=NotificationMotif.CANDIDATURE_STATUT,
                document_concerne=None,
                objet=objet,
                corps=corps,
            ),
            actor=reviewer,
        )

        logger.info(
            "application_decided",
            extra={"application_id": application.pk, "accepted": dto.accept, "reviewer_id": reviewer.pk},
        )
        return application
