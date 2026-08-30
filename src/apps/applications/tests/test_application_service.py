"""Tests ciblant le scénario discuté : un candidat qui a validé son M1 dans
un Master X veut postuler en 2e année dans un Master Y (passerelle), et le
cas où les documents requis ne sont pas tous approuvés."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.apps.applications.dto.application import SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import (
    AlreadyApplied,
    MasterNotOpen,
    MissingRequiredDocuments,
    NotEligible,
)
from src.apps.applications.services.application_service import ApplicationService


def _master(statut="OUVERT", pk=1, required_types=(), passerelles_depuis_ids=(), type_licences_ids=()):
    return SimpleNamespace(
        pk=pk,
        id=pk,
        statut=statut,
        nom="Master IA",
        required_documents=SimpleNamespace(
            filter=lambda deleted_at__isnull: SimpleNamespace(
                values_list=lambda field, flat: list(required_types)
            )
        ),
        type_licences_acceptees=SimpleNamespace(
            filter=lambda pk: SimpleNamespace(exists=lambda: pk in type_licences_ids)
        ),
        passerelles_depuis=SimpleNamespace(
            filter=lambda pk: SimpleNamespace(exists=lambda: pk in passerelles_depuis_ids)
        ),
    )


def _profile(pk=10, diplome=None, master1_year=None):
    return SimpleNamespace(pk=pk, id=pk, pubkey="cand_1", user=SimpleNamespace(pk=999), diplome=diplome, master1_year=master1_year)


def test_resolve_niveau_m2_via_passerelle_when_m1_linked_to_master_x():
    """Le coeur du scénario : M1 validé dans Master X (sur la plateforme,
    donc `master1_year.master_id` renseigné), Master X a une passerelle
    déclarée vers Master Y -> le candidat peut postuler "M2" à Master Y."""
    profile = _profile(diplome=None, master1_year=SimpleNamespace(master_id=7))
    master_y = _master(passerelles_depuis_ids=(7,))

    niveau = ApplicationService._resolve_niveau(profile, master_y)

    assert niveau == "M2"


def test_resolve_niveau_m2_when_m1_done_externally_pending_manual_review():
    """M1 fait hors plateforme (master_id=None) : pas de vérification
    automatique possible, mais la candidature est acceptée en "M2" en
    attente de validation manuelle par un coordinateur (documents
    justificatifs à l'appui, gérés séparément)."""
    profile = _profile(diplome=None, master1_year=SimpleNamespace(master_id=None))
    master_y = _master(passerelles_depuis_ids=())

    niveau = ApplicationService._resolve_niveau(profile, master_y)

    assert niveau == "M2"


def test_resolve_niveau_not_eligible_without_diplome_or_m1():
    profile = _profile(diplome=None, master1_year=None)
    master_y = _master()

    with pytest.raises(NotEligible):
        ApplicationService._resolve_niveau(profile, master_y)


def test_resolve_niveau_m1_when_diplome_type_licence_accepted():
    profile = _profile(diplome=SimpleNamespace(type_licence_id=3), master1_year=None)
    master = _master(type_licences_ids=(3,))

    assert ApplicationService._resolve_niveau(profile, master) == "M1"


@pytest.mark.django_db
@patch("src.apps.applications.services.application_service.NotificationService")
@patch("src.apps.applications.services.application_service.candidate_has_approved_type")
@patch("src.apps.applications.services.application_service.Application")
@patch("src.apps.applications.services.application_service.get_active_for_candidate_and_master")
def test_submit_raises_missing_required_documents(
    mock_get_active, mock_application_cls, mock_has_approved, mock_notification_service
):
    profile = _profile(diplome=SimpleNamespace(type_licence_id=3), master1_year=None)
    master = _master(type_licences_ids=(3,), required_types=["DIPLOME", "RELEVE_NOTES"])
    mock_get_active.return_value = None
    mock_has_approved.side_effect = lambda profile_id, doc_type: doc_type == "DIPLOME"

    with patch("src.apps.masters.models.Master") as mock_master_cls, \
         patch("src.apps.masters.models.MasterStatus") as mock_status:
        mock_status.OUVERT = "OUVERT"
        mock_master_cls.objects.select_for_update.return_value.filter.return_value.first.return_value = master

        with pytest.raises(MissingRequiredDocuments):
            ApplicationService.submit(profile, SubmitApplicationDTO(master_pubkey="mst_y"))


@pytest.mark.django_db
@patch("src.apps.applications.services.application_service.get_active_for_candidate_and_master")
def test_submit_raises_already_applied(mock_get_active):
    profile = _profile()
    master = _master()
    mock_get_active.return_value = SimpleNamespace(pk=1)

    with patch("src.apps.masters.models.Master") as mock_master_cls, \
         patch("src.apps.masters.models.MasterStatus") as mock_status:
        mock_status.OUVERT = "OUVERT"
        mock_master_cls.objects.select_for_update.return_value.filter.return_value.first.return_value = master

        with pytest.raises(AlreadyApplied):
            ApplicationService.submit(profile, SubmitApplicationDTO(master_pubkey="mst_y"))
