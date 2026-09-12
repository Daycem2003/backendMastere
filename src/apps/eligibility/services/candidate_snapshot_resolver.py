from src.apps.eligibility.domain.candidate_snapshot import CandidateSnapshot


def build_snapshot_from_candidate_profile(profile) -> CandidateSnapshot:
    diplome = getattr(profile, "diplome", None)
    if not diplome and hasattr(profile, "diplomes"):
        diplome = profile.diplomes.first()
    redoublement = getattr(profile, "redoublement", None)

    return CandidateSnapshot(
        licence_type_code=diplome.type_licence.pubkey if (diplome and diplome.type_licence) else None,
        average=_calculate_average(profile),
        repeated_years=(
            redoublement.redoublement_years.count() if redoublement and redoublement.a_redouble else 0
        ),
        nationality=getattr(profile, "nationalite", None),
        university_name=diplome.universite if diplome else None,
        graduation_date=None,
        date_of_birth=None,
    )


def _calculate_average(profile) -> float | None:
    years = list(profile.licence_years.all())
    if not years:
        return None
    return sum(float(y.moyenne) for y in years) / len(years)
