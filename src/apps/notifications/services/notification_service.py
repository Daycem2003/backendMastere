import logging
import uuid

from django.db import transaction

from src.apps.candidate_profile.models import CandidateProfile
from src.apps.masters.models import Application
from src.apps.notifications.dto.notification import NotifyDocumentIssueDTO
from src.apps.notifications.exceptions.notification_exceptions import (
    ApplicationDoesNotBelongToCandidate,
    ApplicationNotFound,
    CandidateProfileNotFound,
    NotificationNotFound,
)
from src.apps.notifications.models import NotificationRecord
from src.apps.notifications.selectors.notification_selector import get_by_pubkey
from src.apps.websocket_events.emitter import notify_user

logger = logging.getLogger(__name__)

NOTIFICATION_CREATED_EVENT = "notification:new"


class NotificationService:
    @staticmethod
    @transaction.atomic
    def notify_document_issue(payload: NotifyDocumentIssueDTO, actor) -> NotificationRecord:
        """Couvre les deux cas :
        - `application_pubkey` absent -> notification liée au profil
          (documents soumis à la création, avant toute candidature).
        - `application_pubkey` présent -> notification liée à cette
          candidature précise (ex: document rejeté pour ce master-là).
        """
        candidate = CandidateProfile.objects.filter(
            pubkey=payload.candidate_profile_pubkey
        ).first()
        if not candidate:
            raise CandidateProfileNotFound()

        application = None
        if payload.application_pubkey:
            application = Application.objects.filter(pubkey=payload.application_pubkey).first()
            if not application:
                raise ApplicationNotFound()
            if application.candidate_profile_id != candidate.id:
                raise ApplicationDoesNotBelongToCandidate()

        record = NotificationRecord.objects.create(
            pubkey=f"notif_{uuid.uuid4().hex[:24]}",
            candidate_profile=candidate,
            application=application,
            motif=payload.motif,
            document_concerne=payload.document_concerne,
            objet=payload.objet,
            corps=payload.corps,
        )

        notify_user(
            user_id=candidate.user_id,
            event=NOTIFICATION_CREATED_EVENT,
            payload={
                "notification_pubkey": record.pubkey,
                "motif": record.motif,
                "document_concerne": record.document_concerne,
                "objet": record.objet,
                "corps": record.corps,
                "application_pubkey": application.pubkey if application else None,
                "envoyee_le": record.envoyee_le.isoformat(),
            },
        )

        logger.info(
            "notification_sent",
            extra={
                "notification_id": record.pk,
                "candidate_profile_id": candidate.id,
                "actor_id": actor.pk,
                "motif": record.motif,
            },
        )
        return record

    @staticmethod
    def mark_as_read(pubkey: str, user) -> NotificationRecord:
        from django.utils import timezone

        record = get_by_pubkey(pubkey)
        if not record:
            raise NotificationNotFound()
        if record.candidate_profile.user_id != user.pk:
            raise NotificationNotFound()  # pas d'information sur l'existence à un tiers
        if record.lu_le is None:
            record.lu_le = timezone.now()
            record.save(update_fields=["lu_le"])
        return record
