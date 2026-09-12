import logging
import uuid

from django.contrib.auth.hashers import make_password
from django.db import transaction

from src.apps.authentication.services.account_activation_service import (
    AccountActivationService,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    CandidateProfileNotFound,
)
from src.apps.candidate_profile.models import CandidateProfile, CandidateStatus
from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_pubkey
from src.apps.documents.models import (
    DocumentReviewStatus,
    DocumentSlot,
    DocumentVersion,
)
from src.apps.documents.serializers.document import format_slot_display_name
from src.apps.notifications.models import NotificationMotif, NotificationRecord
from src.apps.notifications.services.email_notification_service import (
    EmailNotificationService,
)
from src.apps.users.dto.user import CreateUserIdentityDTO
from src.apps.users.models import User
from src.apps.users.services.user_provisioning_service import UserProvisioningService

logger = logging.getLogger(__name__)


class CoordinatorDecisionService:
    @classmethod
    @transaction.atomic
    def approve_candidature(cls, pubkey: str, actor_user) -> CandidateProfile:
        profile = get_by_pubkey(pubkey)
        if not profile:
            raise CandidateProfileNotFound()

        # 1. Mise à jour du statut
        profile.statut = CandidateStatus.VALIDE

        # 2. Création ou association du compte User si inexistant
        if not profile.user:
            existing_user = User.objects.filter(email=profile.email, deleted_at__isnull=True).first()
            if existing_user:
                user = existing_user
            else:
                user = UserProvisioningService.create_user_with_role(
                    identity_dto=CreateUserIdentityDTO(
                        email=profile.email,
                        password_hash=make_password(None),
                    ),
                    role_code="CANDIDATE",
                    assigned_by=actor_user if actor_user and actor_user.is_authenticated else None,
                )
            profile.user = user
            profile.save(update_fields=["statut", "user"])
        else:
            user = profile.user
            profile.save(update_fields=["statut"])

        # 3. Génération du token d'activation (usage unique, 48h)
        activation_record = AccountActivationService.create_activation_token(user)

        # 4. Envoi de l'email de notification avec le lien d'activation
        EmailNotificationService.notify_candidate_approved(
            candidate_profile=profile,
            activation_token=activation_record.token,
        )

        # 5. Création d'une trace de notification in-app
        NotificationRecord.objects.create(
            pubkey=f"notif_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            motif=NotificationMotif.CANDIDATURE_STATUT,
            objet="Candidature validée",
            corps="Votre dossier de candidature a été validé. Un email avec le lien d'activation de compte vous a été envoyé.",
        )

        logger.info(
            "candidate_approved",
            extra={"profile_pubkey": profile.pubkey, "actor_id": actor_user.pk if actor_user else None},
        )
        return profile

    @classmethod
    @transaction.atomic
    def reject_candidature(
        cls, pubkey: str, motif: str | None, actor_user
    ) -> CandidateProfile:
        profile = get_by_pubkey(pubkey)
        if not profile:
            raise CandidateProfileNotFound()

        profile.statut = CandidateStatus.REJETE
        profile.save(update_fields=["statut"])

        # Envoi de l'email de notification
        EmailNotificationService.notify_candidate_rejected(
            candidate_profile=profile,
            motif=motif,
        )

        # Notification in-app
        corps = "Votre candidature n'a pas été retenue."
        if motif:
            corps += f" Motif: {motif}"

        NotificationRecord.objects.create(
            pubkey=f"notif_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            motif=NotificationMotif.CANDIDATURE_STATUT,
            objet="Candidature non retenue",
            corps=corps,
        )

        logger.info(
            "candidate_rejected",
            extra={
                "profile_pubkey": profile.pubkey,
                "motif": motif,
                "actor_id": actor_user.pk if actor_user else None,
            },
        )
        return profile

    @classmethod
    @transaction.atomic
    def request_revision(
        cls,
        pubkey: str,
        message: str | None,
        actor_user,
        documents_a_redeposer: list[str] | None = None,
    ) -> CandidateProfile:
        profile = get_by_pubkey(pubkey)
        if not profile:
            raise CandidateProfileNotFound()

        clean_message = (message or "").strip()
        profile.statut = CandidateStatus.A_REVISER
        profile.latest_revision_message = clean_message
        profile.save(update_fields=["statut", "latest_revision_message", "updated_at"])

        # Gestion des documents ciblés à redéposer
        targeted_keys = set(documents_a_redeposer or [])
        targeted_doc_names: list[str] = []

        slots = DocumentSlot.objects.filter(candidate_profile=profile)
        for slot in slots:
            active_version = DocumentVersion.objects.filter(
                slot=slot, is_active=True, deleted_at__isnull=True
            ).first()

            is_targeted = False
            if targeted_keys:
                is_targeted = (slot.pubkey in targeted_keys) or (
                    active_version is not None and active_version.pubkey in targeted_keys
                )

            if is_targeted:
                if not slot.a_redeposer:
                    slot.a_redeposer = True
                    slot.save(update_fields=["a_redeposer", "updated_at"])
                if active_version:
                    active_version.status = DocumentReviewStatus.REJECTED
                    active_version.rejection_reason = clean_message or "À redéposer suite à la demande de révision"
                    active_version.save(update_fields=["status", "rejection_reason"])

                doc_name = format_slot_display_name(
                    slot.type,
                    slot.domaine,
                    slot.annee_licence,
                    slot.redoublement_annee,
                    slot.justificatif_index,
                )
                targeted_doc_names.append(doc_name)
            else:
                if slot.a_redeposer:
                    slot.a_redeposer = False
                    slot.save(update_fields=["a_redeposer", "updated_at"])

        # Envoi de l'email de révision
        EmailNotificationService.notify_candidate_revision_needed(
            candidate_profile=profile,
            message=clean_message,
            onboarding_token=profile.onboarding_token,
            targeted_documents=targeted_doc_names,
        )

        # Notification in-app
        corps = clean_message
        if targeted_doc_names:
            docs_summary = "\n• " + "\n• ".join(targeted_doc_names)
            if corps:
                corps += f"\n\nPièces à redéposer :{docs_summary}"
            else:
                corps = f"Veuillez redéposer les pièces suivantes :{docs_summary}"

        NotificationRecord.objects.create(
            pubkey=f"notif_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            motif=NotificationMotif.DOCUMENT_MANQUANT,
            objet="Demande de révision de votre dossier",
            corps=corps or "Des modifications ont été demandées sur votre dossier de candidature.",
        )

        logger.info(
            "candidate_revision_requested",
            extra={
                "profile_pubkey": profile.pubkey,
                "targeted_documents_count": len(targeted_doc_names),
                "actor_id": actor_user.pk if actor_user else None,
            },
        )
        return profile
