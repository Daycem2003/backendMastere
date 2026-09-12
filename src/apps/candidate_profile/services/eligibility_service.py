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
        diplome = getattr(profile, "diplome", None)
        if not diplome and hasattr(profile, "diplomes") and hasattr(profile.diplomes, "all"):
            diplome = profile.diplomes.first()
        if not diplome:
            return False
        tl_id = getattr(diplome, "type_licence_id", None)
        if tl_id is None and getattr(diplome, "type_licence", None):
            tl_id = getattr(diplome.type_licence, "pk", None) or getattr(diplome.type_licence, "id", None)
        if tl_id is None:
            return False
        return bool(master.type_licences_acceptees.filter(pk=tl_id).exists())

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
