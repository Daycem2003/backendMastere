from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.apps.documents.models import DocumentReviewStatus
from src.apps.documents.services.document_service import DocumentService


def test_rejection_requires_reason():
    with pytest.raises(Exception):
        DocumentService.reject(1, SimpleNamespace(pk=2), "")


def test_can_candidate_apply_requires_every_required_type():
    with patch(
        "src.apps.documents.services.document_service.candidate_has_approved_slots_of_type",
        side_effect=lambda candidate_id, slot_type: slot_type == "DIPLOME",
    ):
        assert DocumentService.can_candidate_apply(1, ["DIPLOME"]) is True
        assert DocumentService.can_candidate_apply(1, ["DIPLOME", "RELEVE_NOTES"]) is False


def test_initial_status_is_pending_review():
    assert DocumentReviewStatus.PENDING_REVIEW == "PENDING_REVIEW"