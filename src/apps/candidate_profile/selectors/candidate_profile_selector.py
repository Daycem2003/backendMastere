from django.db.models import Q

from src.apps.candidate_profile.models import CandidateProfile, TypeLicence


def list_candidate_profiles(statut: str | None = None, q: str | None = None):
    qs = (
        CandidateProfile.objects.select_related(
            "master1_year", "master1_year__master", "redoublement"
        )
        .prefetch_related("diplomes", "diplomes__type_licence", "licence_years", "licence_years__type_licence", "redoublement__redoublement_years")
        .filter(deleted_at__isnull=True)
    )

    if statut and statut.strip() and statut.upper() != "TOUS":
        qs = qs.filter(statut=statut.strip().upper())

    if q and q.strip():
        search = q.strip()
        qs = qs.filter(
            Q(nom__icontains=search)
            | Q(prenom__icontains=search)
            | Q(cin__icontains=search)
            | Q(email__icontains=search)
            | Q(ville__icontains=search)
        )

    return qs.order_by("-created_at")


def get_by_pubkey(pubkey: str) -> CandidateProfile | None:
    return (
        CandidateProfile.objects.select_related(
            "master1_year", "master1_year__master", "redoublement"
        )
        .prefetch_related("diplomes", "diplomes__type_licence", "licence_years", "licence_years__type_licence", "redoublement__redoublement_years")
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