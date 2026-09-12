from django.db import models

from src.apps.candidate_profile.models import CandidateProfile, CandidateStatus
from src.apps.users.models import User, UserRole
from src.shared.models import TimestampedSoftDeleteModel


class AccountActivationToken(TimestampedSoftDeleteModel):
    """Jeton d'activation à usage unique et expirable pour permettre à un
    candidat dont le profil a été validé de définir son mot de passe et
    d'activer son compte."""

    pubkey = models.TextField(unique=True)
    token = models.TextField(unique=True, db_index=True)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="activation_tokens",
        db_column="userId",
    )
    expires_at = models.DateTimeField(db_column="expiresAt")
    used_at = models.DateTimeField(null=True, blank=True, db_column="usedAt")

    class Meta:
        managed = True
        db_table = "MST_ACCOUNT_ACTIVATION_TOKENS"


UserModel = User
CandidateProfileModel = CandidateProfile
UserRoleEnum = UserRole
CandidateStatusEnum = CandidateStatus

__all__ = [
    "AccountActivationToken",
    "UserModel",
    "CandidateProfileModel",
    "UserRoleEnum",
    "CandidateStatusEnum",
]
