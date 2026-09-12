import logging
import uuid

from django.db import transaction

from src.apps.applications.dto.application import DecisionDTO, SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import (
    AlreadyApplied,
    ApplicationAlreadyDecided,
    ApplicationNotWithdrawable,
    CandidateProfileRequired,
    MasterNotFound,
    MasterNotOpen,
    MissingRequiredDocuments,
    NotEligible,
)
from src.apps.applications.models import Application, ApplicationStatus
from src.apps.applications.selectors.application_selector import get_active_for_candidate_and_master
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.candidate_profile.services.eligibility_service import EligibilityService
from src.apps.documents.selectors.document_selector import candidate_has_approved_slots_of_type
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
    def recalculate_ranks_for_master(master_id: int) -> None:
        """Recalcule et met à jour le rang de toutes les candidatures actives
        pour un Master donné, classées par score décroissant puis date de création."""
        from django.db.models import F

        applications = list(
            Application.objects.filter(master_id=master_id, deleted_at__isnull=True).order_by(
                F("score").desc(nulls_last=True), "created_at"
            )
        )
        for index, app in enumerate(applications, start=1):
            app.rang = index
        Application.objects.bulk_update(applications, ["rang"])

    @staticmethod
    @transaction.atomic
    def submit(profile: CandidateProfile, dto: SubmitApplicationDTO) -> Application:
        from src.apps.masters.models import Master, MasterStatus  # import tardif, évite le couplage au chargement

        if getattr(profile, "statut", None) != "VALIDE":
            raise CandidateProfileRequired("Votre profil candidat doit être validé par la commission avant de pouvoir postuler.")

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

        # Vérification d'éligibilité complète via le moteur de règles d'éligibilité
        from src.apps.eligibility.services.candidate_snapshot_resolver import build_snapshot_from_candidate_profile
        from src.apps.eligibility.services.eligibility_evaluation_service import EligibilityService as EligibilityRuleEngine

        snapshot = build_snapshot_from_candidate_profile(profile, master)
        eval_result = EligibilityRuleEngine.evaluate(snapshot, master)
        if not eval_result.eligible:
            failed_descriptions = []
            failed_criteria = []
            for r in eval_result.failed_rules:
                if r.criterion == "average":
                    desc = f"Moyenne minimale de Licence requise : {r.expected} (votre moyenne : {r.actual})"
                elif r.criterion == "nationality":
                    desc = f"Nationalité requise : {r.expected} (votre nationalité : {r.actual})"
                elif r.criterion == "licence_type":
                    desc = f"Type de licence requis : {r.expected} (votre licence : {r.actual})"
                else:
                    desc = f"Critère '{r.criterion}' non satisfait : {r.reason} (Attendu : {r.expected}, Actuel : {r.actual})"
                failed_descriptions.append(desc)
                failed_criteria.append({
                    "criterion": r.criterion,
                    "expected": r.expected,
                    "actual": r.actual,
                    "reason": r.reason,
                    "description": desc,
                })
            raise NotEligible(
                detail=f"Candidat inéligible pour ce Master : {'; '.join(failed_descriptions)}",
                failed_criteria=failed_criteria,
            )

        required_types = list(
            master.required_documents.filter(deleted_at__isnull=True).values_list("type", flat=True)
        )
        missing = [
            t for t in required_types if not candidate_has_approved_slots_of_type(profile.id, t)
        ]
        if missing:
            raise MissingRequiredDocuments(missing_types=missing)

        # Calcul automatique du score
        from src.apps.scoring.services.scoring_service import ApplicationScoringService

        score = ApplicationScoringService.calculate_score(profile, master)

        application = Application.objects.create(
            pubkey=f"app_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            master=master,
            niveau=niveau,
            score=score,
        )

        # Recalculer le rang de toutes les candidatures pour ce Master
        ApplicationService.recalculate_ranks_for_master(master.id)
        application.refresh_from_db()

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
            extra={"application_id": application.pk, "candidate_profile_id": profile.id, "master_id": master.id, "rang": application.rang},
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
