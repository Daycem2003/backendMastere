from src.apps.applications.models import Application
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.masters.models import Master


def get_owner_user_id_of_master(master_pubkey: str) -> int | None:
    return Master.objects.filter(pubkey=master_pubkey).values_list("coordinateur__user_id", flat=True).first()


def get_owner_user_id_of_candidate_profile(candidate_profile_pubkey: str) -> int | None:
    return CandidateProfile.objects.filter(pubkey=candidate_profile_pubkey).values_list("user_id", flat=True).first()


def get_owner_user_id_of_application(application_pubkey: str) -> int | None:
    return Application.objects.filter(pubkey=application_pubkey).values_list("candidate_profile__user_id", flat=True).first()


def is_self(user, target_user_id: int) -> bool:
    return user.id == target_user_id
