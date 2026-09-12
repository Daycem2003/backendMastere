from src.apps.eligibility.domain.candidate_snapshot import CandidateSnapshot


def build_snapshot_from_candidate_profile(profile, master=None) -> CandidateSnapshot:
    diplomes = []
    if hasattr(profile, "diplomes"):
        d_attr = getattr(profile, "diplomes")
        if hasattr(d_attr, "select_related"):
            diplomes = list(d_attr.select_related("type_licence").all())
        elif hasattr(d_attr, "all"):
            res = d_attr.all()
            diplomes = list(res) if isinstance(res, (list, tuple)) else list(res.all())
        elif isinstance(d_attr, (list, tuple)):
            diplomes = list(d_attr)
    if not diplomes and getattr(profile, "diplome", None):
        diplomes = [profile.diplome]

    # Si un master est spécifié, privilégier le diplôme dont le TypeLicence est accepté par ce master
    matching_diplome = None
    if master and hasattr(master, "type_licences_acceptees"):
        accepted_pubkeys = set(master.type_licences_acceptees.values_list("pubkey", flat=True)) if hasattr(master.type_licences_acceptees, "values_list") else set()
        for d in diplomes:
            tl = getattr(d, "type_licence", None)
            if tl and getattr(tl, "pubkey", None) in accepted_pubkeys:
                matching_diplome = d
                break

    diplome = matching_diplome or (diplomes[0] if diplomes else None)
    redoublement = getattr(profile, "redoublement", None)

    tl = getattr(diplome, "type_licence", None) if diplome else None
    licence_type_code = getattr(tl, "pubkey", None) if tl else None
    if not licence_type_code and diplome and getattr(diplome, "type_licence_id", None):
        licence_type_code = str(diplome.type_licence_id)

    return CandidateSnapshot(
        licence_type_code=licence_type_code,
        average=_calculate_average(profile, diplome),
        repeated_years=(
            redoublement.redoublement_years.count()
            if redoublement and getattr(redoublement, "a_redouble", False) and hasattr(redoublement, "redoublement_years")
            else 0
        ),
        nationality=getattr(profile, "nationalite", None),
        university_name=getattr(diplome, "universite", None) if diplome else None,
        graduation_date=None,
        date_of_birth=None,
    )


def _calculate_average(profile, diplome=None) -> float | None:
    years = list(profile.licence_years.all())
    if not years:
        return None
    if diplome and getattr(diplome, "type_licence_id", None):
        filtered = [
            y
            for y in years
            if getattr(y, "type_licence_id", None) == diplome.type_licence_id
            or not getattr(y, "type_licence_id", None)
        ]
        if filtered:
            years = filtered
    return round(sum(float(y.moyenne) for y in years) / len(years), 2)
