import logging
import uuid

from django.db import transaction

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateCandidateProfileDTO,
    UpdateCandidateProfileDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    ProfileAlreadyExists,
    ProfileNotEditable,
)
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.candidate_profile.policies.candidate_profile_policy import CandidateProfilePolicy
from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_user

logger = logging.getLogger(__name__)


class CandidateProfileService:
    @staticmethod
    @transaction.atomic
    def create_profile(dto: CreateCandidateProfileDTO, user) -> CandidateProfile:
        if get_by_user(user) is not None:
            raise ProfileAlreadyExists()

        profile = CandidateProfile.objects.create(
            pubkey=f"cand_{uuid.uuid4().hex[:24]}",
            user=user,
            nom=dto.nom,
            prenom=dto.prenom,
            cin=dto.cin,
            email=dto.email,
            telephone=dto.telephone,
            ville=dto.ville,
            annee_naissance=dto.annee_naissance,
        )
        logger.info("candidate_profile_created", extra={"profile_id": profile.pk, "user_id": user.pk})
        return profile

    @staticmethod
    def update_profile(profile: CandidateProfile, dto: UpdateCandidateProfileDTO, user) -> CandidateProfile:
        if not CandidateProfilePolicy.can_edit(user, profile):
            raise ProfileNotEditable()

        fields = []
        if dto.telephone is not None:
            profile.telephone = dto.telephone
            fields.append("telephone")
        if dto.ville is not None:
            profile.ville = dto.ville
            fields.append("ville")
        if fields:
            profile.save(update_fields=fields)
        return profile
