from src.apps.candidate_profile.models import CandidateProfile, TypeLicence


def get_by_pubkey(pubkey: str) -> CandidateProfile | None:
    return (
        CandidateProfile.objects.select_related(
            "diplome", "diplome__type_licence", "master1_year", "master1_year__master", "redoublement"
        )
        .prefetch_related("licence_years", "redoublement__redoublement_years")
        .filter(pubkey=pubkey, deleted_at__isnull=True)
        .first()
    )


def get_by_user(user) -> CandidateProfile | None:
    return CandidateProfile.objects.filter(user_id=user.pk, deleted_at__isnull=True).first()


def get_eligible_type_licence(pubkey: str) -> TypeLicence | None:
    return TypeLicence.objects.filter(
        pubkey=pubkey, est_eligible=True, deleted_at__isnull=True
    ).first()
