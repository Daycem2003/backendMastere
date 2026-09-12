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


def get_by_user(user) -> CandidateProfile | None:
    if user is None or not getattr(user, "is_authenticated", True) or not getattr(user, "pk", None):
        return None

    qs = (
        CandidateProfile.objects.select_related(
            "master1_year", "master1_year__master", "redoublement"
        )
        .prefetch_related(
            "diplomes",
            "diplomes__type_licence",
            "licence_years",
            "licence_years__type_licence",
            "redoublement__redoublement_years",
        )
        .filter(deleted_at__isnull=True)
    )

    # 1. Priorité absolue : association directe OneToOne par user_id
    profile = qs.filter(user_id=user.pk).first()
    if profile:
        return profile

    # 2. Repli par email si renseigné et non vide
    user_email = getattr(user, "email", None)
    if user_email and isinstance(user_email, str) and user_email.strip():
        profile = qs.filter(email__iexact=user_email.strip()).first()
        if profile:
            if profile.user_id is None:
                profile.user = user
                profile.save(update_fields=["user"])
            return profile

    return None


def get_by_onboarding_token(token: str | None) -> CandidateProfile | None:
    """Résout un profil candidat via son jeton d'onboarding — utilisé
    pendant tout le parcours de création (avant que le candidat ait un
    compte), pour enchaîner les appels licence-years/diplome/master1-year/
    redoublement sur le même profil sans authentification.
    """
    if not token or not isinstance(token, str):
        return None

    token_clean = token.strip()
    if not token_clean or token_clean.lower() in ("null", "undefined", "none"):
        return None

    return (
        CandidateProfile.objects.select_related(
            "master1_year", "master1_year__master", "redoublement"
        )
        .prefetch_related(
            "diplomes",
            "diplomes__type_licence",
            "licence_years",
            "licence_years__type_licence",
            "redoublement__redoublement_years",
            "document_slots",
            "document_slots__versions",
        )
        .filter(onboarding_token=token_clean, deleted_at__isnull=True)
        .first()
    )



def get_eligible_type_licence(pubkey: str) -> TypeLicence | None:
    return TypeLicence.objects.filter(
        pubkey=pubkey, est_eligible=True, deleted_at__isnull=True
    ).first()