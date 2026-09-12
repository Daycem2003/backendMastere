import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from src.apps.candidate_profile.models import CandidateProfile

logger = logging.getLogger(__name__)


class EmailNotificationService:
    @staticmethod
    def _send_templated_email(
        subject: str,
        to_email: str,
        template_name: str,
        context: dict,
    ) -> bool:
        try:
            html_content = render_to_string(f"emails/{template_name}.html", context)
            text_content = render_to_string(f"emails/{template_name}.txt", context)

            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@mastertn.tn")
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            logger.info("email_sent_successfully", extra={"to": to_email, "template": template_name})
            return True
        except Exception as exc:
            logger.error(
                "failed_to_send_email",
                extra={"to": to_email, "template": template_name, "error": str(exc)},
                exc_info=True,
            )
            return False

    @classmethod
    def notify_candidate_approved(
        cls, candidate_profile: CandidateProfile, activation_token: str
    ) -> bool:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080").rstrip("/")
        activation_link = f"{frontend_url}/activer-compte?token={activation_token}"
        candidate_name = f"{candidate_profile.prenom} {candidate_profile.nom}".strip() or candidate_profile.email

        context = {
            "candidate_name": candidate_name,
            "activation_link": activation_link,
            "candidate_profile": candidate_profile,
        }
        return cls._send_templated_email(
            subject="[Mastères] Votre dossier a été approuvé — Activez votre compte",
            to_email=candidate_profile.email,
            template_name="approval",
            context=context,
        )

    @classmethod
    def notify_candidate_rejected(
        cls, candidate_profile: CandidateProfile, motif: str | None = None
    ) -> bool:
        candidate_name = f"{candidate_profile.prenom} {candidate_profile.nom}".strip() or candidate_profile.email

        context = {
            "candidate_name": candidate_name,
            "motif": motif,
            "candidate_profile": candidate_profile,
        }
        return cls._send_templated_email(
            subject="[Mastères] Décision concernant votre candidature",
            to_email=candidate_profile.email,
            template_name="rejection",
            context=context,
        )

    @classmethod
    def notify_candidate_revision_needed(
        cls,
        candidate_profile: CandidateProfile,
        message: str,
        onboarding_token: str,
        targeted_documents: list[str] | None = None,
    ) -> bool:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080").rstrip("/")
        revision_link = f"{frontend_url}/profil/creer?token={onboarding_token}"
        candidate_name = f"{candidate_profile.prenom} {candidate_profile.nom}".strip() or candidate_profile.email

        context = {
            "candidate_name": candidate_name,
            "message": message,
            "revision_link": revision_link,
            "candidate_profile": candidate_profile,
            "targeted_documents": targeted_documents or [],
        }
        return cls._send_templated_email(
            subject="[Mastères] Complément d'information requis pour votre candidature",
            to_email=candidate_profile.email,
            template_name="revision_request",
            context=context,
        )
