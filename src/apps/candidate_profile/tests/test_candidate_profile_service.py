from types import SimpleNamespace
from unittest.mock import patch

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
from src.apps.candidate_profile.dto.candidate_profile import CreateCandidateProfileDTO
# pyrefly: ignore [missing-import]
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    ProfileAlreadyExists,
)
# pyrefly: ignore [missing-import]
from src.apps.candidate_profile.services.candidate_profile_service import (
    CandidateProfileService,
)

pytestmark = pytest.mark.django_db

def _dto(**overrides):
    base = {
        "nom": "Ben Ali",
        "prenom": "Sami",
        "cin": "12345678",
        "email": "sami@example.com",
        "telephone": "20123456",
        "ville": "Tunis",
        "nationalite": "Tunisienne",
        "annee_naissance": 2000,
    }
    base.update(overrides)
    return CreateCandidateProfileDTO(**base)

@patch("src.apps.candidate_profile.services.candidate_profile_service.get_by_user")
def test_create_profile_raises_if_already_exists(mock_get_by_user):
    mock_get_by_user.return_value = SimpleNamespace(pk=1)

    with pytest.raises(ProfileAlreadyExists):
        CandidateProfileService.create_profile(
        _dto(),
        user=SimpleNamespace(pk=99),
    )

@patch("src.apps.candidate_profile.services.candidate_profile_service.CandidateProfile")
@patch("src.apps.candidate_profile.services.candidate_profile_service.get_by_user")
def test_create_profile_generates_pubkey(mock_get_by_user, mock_model_cls):
    mock_get_by_user.return_value = None
    mock_model_cls.objects.filter.return_value.exists.return_value = False
    created = SimpleNamespace(pk=1)
    mock_model_cls.objects.create.return_value = created
    result = CandidateProfileService.create_profile(
        _dto(),
        user=SimpleNamespace(pk=99),
    )
    assert result is created
    call_kwargs = mock_model_cls.objects.create.call_args.kwargs
    assert call_kwargs["pubkey"].startswith("cand_")
    assert call_kwargs["cin"] == "12345678"

def test_annee_naissance_out_of_range_rejected():
    with pytest.raises(ValueError):
        _dto(annee_naissance=1800)
