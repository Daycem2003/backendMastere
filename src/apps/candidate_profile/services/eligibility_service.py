import logging

from src.apps.candidate_profile.models import CandidateProfile

logger = logging.getLogger(__name__)


class EligibilityService:
    """Vérifie l'éligibilité d'un candidat à un Master donné, y compris le
    cas passerelle M1 -> M2 (cf. discussion sur le schéma) :

    - Si le candidat a un diplôme de licence dont le TypeLicence est
      accepté par le Master visé -> éligible via le parcours classique.
    - Sinon, si le candidat a validé un Master1Year rattaché à un `Master`
      de la plateforme (`Master1Year.master`), et que ce Master a une
      passerelle déclarée vers le Master visé (`Master.passerellesVers`)
      -> éligible via passerelle.
    - Un `Master1Year` sans `master` renseigné (M1 fait hors plateforme)
      ne peut pas être vérifié automatiquement : à traiter manuellement
      par un coordinateur (cf. `RequiredDocument`/justificatifs).
    """

    @staticmethod
    def is_eligible_via_licence(profile: CandidateProfile, master) -> bool:
        diplomes = []
        if hasattr(profile, "diplomes"):
            d_attr = getattr(profile, "diplomes")
            if hasattr(d_attr, "all"):
                res = d_attr.all()
                diplomes = list(res) if isinstance(res, (list, tuple)) else list(res.all())
            elif isinstance(d_attr, (list, tuple)):
                diplomes = list(d_attr)
        if not diplomes and getattr(profile, "diplome", None):
            diplomes = [profile.diplome]

        if not diplomes:
            return False

        if not hasattr(master, "type_licences_acceptees"):
            return True
        tla = master.type_licences_acceptees
        if hasattr(tla, "exists") and not tla.exists():
            return True
        if hasattr(tla, "count") and tla.count() == 0:
            return True
        if hasattr(tla, "all"):
            all_tla = list(tla.all())
            if not all_tla:
                return True

        accepted_pks = set()
        accepted_pubkeys = set()
        if hasattr(tla, "values_list"):
            for v in tla.values_list("pk", flat=True):
                accepted_pks.add(v)
                accepted_pks.add(str(v))
                try:
                    accepted_pks.add(int(v))
                except (ValueError, TypeError):
                    pass
            for v in tla.values_list("pubkey", flat=True):
                accepted_pubkeys.add(str(v))
        if hasattr(tla, "all"):
            for t in tla.all():
                pk_val = getattr(t, "pk", getattr(t, "id", None))
                if pk_val is not None:
                    accepted_pks.add(pk_val)
                    accepted_pks.add(str(pk_val))
                    try:
                        accepted_pks.add(int(pk_val))
                    except (ValueError, TypeError):
                        pass
                pubkey_val = getattr(t, "pubkey", None)
                if pubkey_val:
                    accepted_pubkeys.add(str(pubkey_val))

        for d in diplomes:
            tl_id = getattr(d, "type_licence_id", None)
            if tl_id is None and getattr(d, "type_licence", None):
                tl_id = getattr(d.type_licence, "pk", getattr(d.type_licence, "id", None))
            tl_pubkey = getattr(d.type_licence, "pubkey", None) if getattr(d, "type_licence", None) else None

            if tl_id is not None and (tl_id in accepted_pks or str(tl_id) in accepted_pks):
                return True
            if tl_pubkey and str(tl_pubkey) in accepted_pubkeys:
                return True
            if hasattr(tla, "filter"):
                try:
                    if tl_id is not None and tla.filter(pk=tl_id).exists():
                        return True
                except Exception:
                    pass

        return False

    @staticmethod
    def is_eligible_via_passerelle(profile: CandidateProfile, master) -> bool:
        m1 = getattr(profile, "master1_year", None)
        if not m1 or not m1.master_id:
            return False
        return master.passerelles_depuis.filter(pk=m1.master_id).exists()

    @staticmethod
    def is_eligible(profile: CandidateProfile, master) -> bool:
        return EligibilityService.is_eligible_via_licence(
            profile, master
        ) or EligibilityService.is_eligible_via_passerelle(profile, master)

    @staticmethod
    def requires_manual_review(profile: CandidateProfile) -> bool:
        """True si le candidat a un M1 non rattaché à un Master de la
        plateforme : l'éligibilité en passerelle ne peut alors pas être
        vérifiée automatiquement et doit être validée par un coordinateur
        sur pièces (justificatifs)."""
        m1 = getattr(profile, "master1_year", None)
        return bool(m1 and not m1.master_id)
