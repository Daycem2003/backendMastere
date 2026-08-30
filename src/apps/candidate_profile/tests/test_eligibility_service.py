"""Tests ciblant précisément le correctif discuté : l'éligibilité en
passerelle M1 -> M2 doit être vérifiable automatiquement quand le M1 a été
fait sur un Master de la plateforme (via Master1Year.master), et signalée
comme nécessitant une revue manuelle sinon."""
from types import SimpleNamespace

from src.apps.candidate_profile.services.eligibility_service import EligibilityService


def _master_with_relations(type_licences_ids=(), passerelles_depuis_ids=()):
    return SimpleNamespace(
        type_licences_acceptees=SimpleNamespace(
            filter=lambda pk: SimpleNamespace(exists=lambda: pk in type_licences_ids)
        ),
        passerelles_depuis=SimpleNamespace(
            filter=lambda pk: SimpleNamespace(exists=lambda: pk in passerelles_depuis_ids)
        ),
    )


def test_eligible_via_licence_when_type_licence_accepted():
    profile = SimpleNamespace(diplome=SimpleNamespace(type_licence_id=7))
    master = _master_with_relations(type_licences_ids=(7,))

    assert EligibilityService.is_eligible(profile, master) is True


def test_not_eligible_without_diplome_or_passerelle():
    profile = SimpleNamespace(diplome=None, master1_year=None)
    master = _master_with_relations()

    assert EligibilityService.is_eligible(profile, master) is False


def test_eligible_via_passerelle_when_m1_linked_to_platform_master():
    profile = SimpleNamespace(
        diplome=None,
        master1_year=SimpleNamespace(master_id=3),
    )
    master = _master_with_relations(passerelles_depuis_ids=(3,))

    assert EligibilityService.is_eligible(profile, master) is True


def test_requires_manual_review_when_m1_not_linked_to_a_platform_master():
    profile = SimpleNamespace(master1_year=SimpleNamespace(master_id=None))
    assert EligibilityService.requires_manual_review(profile) is True


def test_no_manual_review_needed_when_m1_linked_or_absent():
    assert EligibilityService.requires_manual_review(SimpleNamespace(master1_year=None)) is False
    assert (
        EligibilityService.requires_manual_review(SimpleNamespace(master1_year=SimpleNamespace(master_id=5)))
        is False
    )
