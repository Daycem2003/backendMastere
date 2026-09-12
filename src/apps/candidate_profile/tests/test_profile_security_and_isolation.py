import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from src.apps.candidate_profile.models import CandidateProfile, CandidateStatus
from src.apps.candidate_profile.selectors.candidate_profile_selector import (
    get_by_user,
    get_by_onboarding_token,
)
from src.apps.candidate_profile.views.academic_record_views import _require_candidate_profile
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import CandidateProfileNotFound
from src.apps.users.models import User
from src.shared.middleware.cache_control_middleware import PrivateNoCacheAPIMiddleware


@pytest.mark.django_db
def test_private_no_cache_api_middleware():
    rf = RequestFactory()
    request = rf.get("/api/v1/candidates/me")

    def dummy_view(req):
        resp = HttpResponse("OK")
        resp["Vary"] = "Accept-Encoding"
        return resp

    middleware = PrivateNoCacheAPIMiddleware(dummy_view)
    response = middleware(request)

    assert "no-cache" in response["Cache-Control"]
    assert "no-store" in response["Cache-Control"]
    assert "private" in response["Cache-Control"]
    assert "Authorization" in response["Vary"]
    assert "X-Onboarding-Token" in response["Vary"]
    assert "Accept-Encoding" in response["Vary"]


@pytest.mark.django_db
def test_get_by_user_isolation_between_two_candidates():
    # User 1
    u1 = User.objects.create(
        pubkey="usr_sec_1",
        email="candidat1@test.tn",
        is_active=True,
    )
    p1 = CandidateProfile.objects.create(
        pubkey="cand_sec_1",
        nom="Ben Salah",
        prenom="Ali",
        cin="09876541",
        email="candidat1@test.tn",
        telephone="22111333",
        ville="Tunis",
        annee_naissance=2000,
        statut=CandidateStatus.VALIDE,
        user=u1,
    )

    # User 2
    u2 = User.objects.create(
        pubkey="usr_sec_2",
        email="candidat2@test.tn",
        is_active=True,
    )
    p2 = CandidateProfile.objects.create(
        pubkey="cand_sec_2",
        nom="Trabelsi",
        prenom="Sonia",
        cin="09876542",
        email="candidat2@test.tn",
        telephone="22111444",
        ville="Sousse",
        annee_naissance=2001,
        statut=CandidateStatus.EN_ATTENTE,
        user=u2,
    )

    # Look up u1
    resolved_1 = get_by_user(u1)
    assert resolved_1 is not None
    assert resolved_1.pubkey == "cand_sec_1"
    assert resolved_1.nom == "Ben Salah"

    # Look up u2
    resolved_2 = get_by_user(u2)
    assert resolved_2 is not None
    assert resolved_2.pubkey == "cand_sec_2"
    assert resolved_2.nom == "Trabelsi"

    # Anonymous / None lookups
    assert get_by_user(None) is None


@pytest.mark.django_db
def test_onboarding_token_security_and_invalid_values():
    assert get_by_onboarding_token(None) is None
    assert get_by_onboarding_token("") is None
    assert get_by_onboarding_token("   ") is None
    assert get_by_onboarding_token("null") is None
    assert get_by_onboarding_token("undefined") is None
    assert get_by_onboarding_token("none") is None

    p = CandidateProfile.objects.create(
        pubkey="cand_sec_tok",
        nom="Kacem",
        prenom="Maha",
        cin="09876549",
        email="maha@test.tn",
        telephone="22111999",
        ville="Monastir",
        annee_naissance=2002,
        statut=CandidateStatus.EN_ATTENTE,
        onboarding_token="valid_secret_token_12345",
    )

    assert get_by_onboarding_token("valid_secret_token_12345") == p


@pytest.mark.django_db
def test_require_candidate_profile_unauthenticated_without_token():
    rf = RequestFactory()
    request = rf.get("/api/v1/candidates/me")
    request.user = None

    with pytest.raises(CandidateProfileNotFound):
        _require_candidate_profile(request)
