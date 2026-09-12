import logging
import secrets
import uuid

from django.db import IntegrityError, transaction

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateCandidateProfileDTO,
    UpdateCandidateProfileDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    ProfileAlreadyExists,
    ProfileNotEditable,
)
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.candidate_profile.policies.candidate_profile_policy import (
    CandidateProfilePolicy,
)
from src.apps.candidate_profile.selectors.candidate_profile_selector import (
    get_by_user,
)

logger = logging.getLogger(__name__)


class CandidateProfileService:
    @staticmethod
    @transaction.atomic
    def create_profile(
        dto: CreateCandidateProfileDTO,
        user=None,
    ) -> CandidateProfile:

        if user is not None and get_by_user(user) is not None:
            raise ProfileAlreadyExists()

        if CandidateProfile.objects.filter(
            cin=dto.cin,
            deleted_at__isnull=True,
        ).exists():
            raise ProfileAlreadyExists()

        try:
            profile = CandidateProfile.objects.create(
                pubkey=f"cand_{uuid.uuid4().hex[:24]}",
                user=user,
                onboarding_token=secrets.token_urlsafe(32),
                nom=dto.nom,
                prenom=dto.prenom,
                cin=dto.cin,
                email=dto.email,
                telephone=dto.telephone,
                ville=dto.ville,
                annee_naissance=dto.annee_naissance,
                nationalite=dto.nationalite,
            )
        except IntegrityError:
            # Filet de sécurité contre une race condition sur la
            # contrainte unique(cin) : deux requêtes concurrentes peuvent
            # toutes deux passer le .exists() ci-dessus avant qu'une seule
            # insertion réussisse. On transforme systématiquement cette
            # violation de contrainte en 400 propre, jamais en 500.
            raise ProfileAlreadyExists()

        logger.info(
            "candidate_profile_created",
            extra={
                "profile_id": profile.pk,
                "user_id": user.pk if user is not None else None,
            },
        )

        return profile

    @staticmethod
    @transaction.atomic
    def update_profile(
        profile: CandidateProfile,
        dto: UpdateCandidateProfileDTO,
        user,
    ) -> CandidateProfile:
        if not CandidateProfilePolicy.can_edit(user, profile):
            raise ProfileNotEditable()

        update_fields: list[str] = []

        if dto.telephone is not None:
            profile.telephone = dto.telephone
            update_fields.append("telephone")

        if dto.ville is not None:
            profile.ville = dto.ville
            update_fields.append("ville")

        if dto.nationalite is not None:
            profile.nationalite = dto.nationalite
            update_fields.append("nationalite")

        if update_fields:
            profile.save(update_fields=update_fields)

        return profile