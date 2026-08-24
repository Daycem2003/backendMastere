from pydantic import BaseModel, Field

from src.apps.notifications.models import NotificationMotif


class NotifyDocumentIssueDTO(BaseModel):
    """Signalement d'un document manquant/frauduleux par un coordinateur.

    - candidate_profile_pubkey : toujours requis (le destinataire réel).
    - application_pubkey : optionnel. Absent = notification liée au profil
      (documents soumis à la création, avant toute candidature).
      Présent = notification liée à une candidature précise.
    """

    candidate_profile_pubkey: str
    application_pubkey: str | None = None
    motif: NotificationMotif
    document_concerne: str | None = Field(default=None, max_length=255)
    objet: str = Field(min_length=1, max_length=255)
    corps: str = Field(min_length=1, max_length=5000)
