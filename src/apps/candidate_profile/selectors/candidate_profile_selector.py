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


def get_by_user(user):
    if user is None:
        return None

    return CandidateProfile.objects.filter(
        user_id=user.pk,
        deleted_at__isnull=True,
    ).first()


def get_by_onboarding_token(token: str | None) -> CandidateProfile | None:
    """Résout un profil candidat via son jeton d'onboarding — utilisé
    pendant tout le parcours de création (avant que le candidat ait un
    compte), pour enchaîner les appels licence-years/diplome/master1-year/
    redoublement sur le même profil sans authentification.
    """
    if not token:
        return None

    return CandidateProfile.objects.filter(
        onboarding_token=token,
        deleted_at__isnull=True,
    ).first()


def get_eligible_type_licence(pubkey: str) -> TypeLicence | None:
    return TypeLicence.objects.filter(
        pubkey=pubkey, est_eligible=True, deleted_at__isnull=True
    ).first()