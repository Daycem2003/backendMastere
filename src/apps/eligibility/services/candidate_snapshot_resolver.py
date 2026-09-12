from src.apps.eligibility.domain.candidate_snapshot import CandidateSnapshot


def build_snapshot_from_candidate_profile(profile) -> CandidateSnapshot:
    
    diplome = getattr(profile, "diplome", None)
    redoublement = getattr(profile, "redoublement", None)

    return CandidateSnapshot(
        licence_type_code=diplome.type_licence.pubkey if diplome else None,
        average=_latest_average(profile),
        repeated_years=(
            redoublement.redoublement_years.count() if redoublement and redoublement.a_redouble else 0
        ),
        nationality=None,  # non modélisé dans candidate_profile actuel — voir README
        university_name=diplome.universite if diplome else None,
        graduation_date=None,  # candidate_profile stocke anneeObtention (str), pas une date -> voir README
        date_of_birth=None,  # candidate_profile stocke anneeNaissance (int), pas une date -> voir README
    )


def _latest_average(profile) -> float | None:
    latest_year = profile.licence_years.order_by("-annee").first()
    return latest_year.moyenne if latest_year else None
