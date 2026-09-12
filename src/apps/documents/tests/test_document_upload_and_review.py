"""Tests ciblant précisément les deux régressions corrigées :

1. Le lookup d'une version doit se faire par SON PROPRE pubkey, pas par
   celui de l'ancien modèle `Document` (souvent None).
2. `create_version`/`store_uploaded_file` doivent réellement appeler le
   storage backend et calculer les métadonnées côté serveur.

NOTE: ce projet n'a pas fourni de conftest.py / factories pour User /
CandidateProfile dans le zip livré. Ces tests mockent donc l'ORM aux points
clés plutôt que de dépendre de fixtures DB réelles, pour rester exécutables
en l'état. L'équipe devrait idéalement les compléter par des tests
end-to-end via APIClient une fois les factories du projet disponibles.
"""
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.apps.documents.exceptions.document_exceptions import (
    FileTooLarge,
    UnsupportedFileType,
)
from src.apps.documents.services.document_service import DocumentService


class _FakeUploadedFile:
    """Simule un django.core.files.uploadedfile.UploadedFile minimal."""

    def __init__(self, name: str, content: bytes, content_type: str):
        self.name = name
        self.content_type = content_type
        self._content = content
        self.size = len(content)

    def chunks(self):
        yield self._content

    def seek(self, offset):
        pass


def test_get_version_by_pubkey_filters_on_documentversion_pubkey():
    """FIX #1 (régression bloquante) : vérifie que le selector interroge
    bien `pubkey=...` sur DocumentVersion, et non `document__pubkey=...`
    (qui échouait pour toute version sans Document legacy lié, i.e. la
    quasi-totalité des uploads normaux)."""
    from src.apps.documents.selectors import document_selector

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.prefetch_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.first.return_value = SimpleNamespace(pubkey="docv_abc123")

    with patch.object(document_selector.DocumentVersion, "objects", mock_qs):
        result = document_selector.get_version_by_pubkey("docv_abc123")

    called_kwargs = mock_qs.filter.call_args.kwargs
    assert "pubkey" in called_kwargs, (
        "get_version_by_pubkey doit filtrer sur DocumentVersion.pubkey, "
        "pas sur document__pubkey"
    )
    assert called_kwargs["pubkey"] == "docv_abc123"
    assert "document__pubkey" not in called_kwargs
    assert result.pubkey == "docv_abc123"


def test_store_uploaded_file_calls_storage_and_computes_metadata_server_side():
    """FIX #2 : le fichier est réellement envoyé au storage backend, et
    mime_type/file_size/checksum sont calculés à partir des octets reçus."""
    fake_file = _FakeUploadedFile("diplome.pdf", b"%PDF-1.4 contenu test", "application/pdf")
    fake_storage = MagicMock()

    fake_profile = SimpleNamespace(nom="BenAli", prenom="Sami", cin="12345678", pubkey="cand_pubkey_1")
    with patch(
        "src.apps.documents.services.document_service.assert_upload_allowed"
    ):
        result = DocumentService.store_uploaded_file(fake_file, fake_profile, fake_storage)

    fake_storage.upload.assert_called_once()
    uploaded_content, uploaded_key = fake_storage.upload.call_args.args
    assert uploaded_content is fake_file
    assert uploaded_key == "BenAli_Sami_12345678/diplome.pdf"
    assert result["mime_type"] == "application/pdf"
    assert result["file_size"] == len(b"%PDF-1.4 contenu test")
    assert len(result["checksum"]) == 64  # sha256 hex digest  # sha256 hex digest


def test_store_uploaded_file_rejects_oversized_file():
    """FIX #2 : la taille n'est plus acceptée telle quelle depuis le client
    — elle est mesurée et plafonnée côté serveur."""
    oversized = _FakeUploadedFile("gros.pdf", b"x" * 10, "application/pdf")
    oversized.size = 999_999_999  # au-delà de MAX_UPLOAD_SIZE_BYTES

    with pytest.raises(FileTooLarge):
        DocumentService.store_uploaded_file(oversized, "cand_pubkey_1", MagicMock())


def test_store_uploaded_file_rejects_unsupported_mime_type():
    """FIX #2 : le mime type est vérifié côté serveur contre une liste
    blanche, pas seulement accepté tel que déclaré par le client."""
    exe_file = _FakeUploadedFile("virus.exe", b"MZ...", "application/x-msdownload")

    with pytest.raises(UnsupportedFileType):
        DocumentService.store_uploaded_file(exe_file, "cand_pubkey_1", MagicMock())


def test_require_candidate_profile_resolves_via_onboarding_token():
    """Vérifie que _require_candidate_profile résout le profil via X-Onboarding-Token
    quand l'utilisateur n'est pas authentifié."""
    from src.apps.documents.views.document_views import _require_candidate_profile
    from src.apps.documents.exceptions.document_exceptions import NoCandidateProfile

    mock_profile = SimpleNamespace(pubkey="cand_profile_123")
    mock_request = SimpleNamespace(
        user=None,
        headers={"X-Onboarding-Token": "valid-onboarding-token"},
    )

    with patch(
        "src.apps.documents.views.document_views.get_by_onboarding_token",
        return_value=mock_profile,
    ) as mock_get_token:
        result = _require_candidate_profile(mock_request)
        mock_get_token.assert_called_once_with("valid-onboarding-token")
        assert result.pubkey == "cand_profile_123"


def test_require_candidate_profile_resolves_via_authenticated_user():
    """Vérifie que _require_candidate_profile résout le profil via l'utilisateur authentifié."""
    from src.apps.documents.views.document_views import _require_candidate_profile

    mock_user = SimpleNamespace(is_authenticated=True, pk=42)
    mock_profile = SimpleNamespace(pubkey="cand_profile_456")
    mock_request = SimpleNamespace(
        user=mock_user,
        headers={},
    )

    with patch(
        "src.apps.documents.views.document_views.get_by_user",
        return_value=mock_profile,
    ) as mock_get_user:
        result = _require_candidate_profile(mock_request)
        mock_get_user.assert_called_once_with(mock_user)
        assert result.pubkey == "cand_profile_456"


def test_require_candidate_profile_raises_when_no_user_and_no_token():
    """Vérifie que NoCandidateProfile est levée en l'absence de user authentifié et de token valide."""
    from src.apps.documents.views.document_views import _require_candidate_profile
    from src.apps.documents.exceptions.document_exceptions import NoCandidateProfile

    mock_request = SimpleNamespace(
        user=None,
        headers={},
    )

    with pytest.raises(NoCandidateProfile):
        _require_candidate_profile(mock_request)


def test_create_version_with_anonymous_actor():
    """Vérifie que create_version gère correctement un acteur anonyme/non authentifié."""
    from src.apps.documents.dto.document import DocumentSlotIdentityDTO, DocumentUploadDTO

    mock_candidate = SimpleNamespace(pubkey="cand_123")
    mock_candidate_qs = MagicMock()
    mock_candidate_qs.select_for_update.return_value = mock_candidate_qs
    mock_candidate_qs.filter.return_value = mock_candidate_qs
    mock_candidate_qs.first.return_value = mock_candidate

    mock_slot = SimpleNamespace(pk=10)
    mock_version = SimpleNamespace(pk=20, pubkey="docv_1")

    dto = DocumentUploadDTO(
        candidate_profile_pubkey="cand_123",
        slot=DocumentSlotIdentityDTO(
            slot_type="RELEVE_LICENCE",
            domaine="Informatique",
            annee_licence="A1",
            redoublement_annee="",
            justificatif_index=0,
        ),
        storage_key="cand_123/test.pdf",
        mime_type="application/pdf",
        file_size=100,
        checksum="abcd" * 16,
    )

    with patch("src.apps.candidate_profile.models.CandidateProfile.objects", mock_candidate_qs), \
         patch("src.apps.documents.models.DocumentSlot.objects.get_or_create", return_value=(mock_slot, True)), \
         patch("src.apps.documents.models.DocumentVersion.objects.select_for_update") as mock_ver_sfu, \
         patch("src.apps.documents.models.DocumentVersion.objects.create", return_value=mock_version) as mock_ver_create, \
         patch("src.apps.documents.models.DocumentAuditEvent.objects.create") as mock_audit_create:

        mock_prev_qs = MagicMock()
        mock_prev_qs.filter.return_value = mock_prev_qs
        mock_prev_qs.order_by.return_value = mock_prev_qs
        mock_prev_qs.first.return_value = None
        mock_ver_sfu.return_value = mock_prev_qs

        anonymous_user = SimpleNamespace(is_authenticated=False)
        fn = getattr(DocumentService.create_version, "__wrapped__", DocumentService.create_version)
        version = fn(dto, anonymous_user)

        assert version == mock_version
        mock_audit_create.assert_called_once_with(
            document_version=mock_version,
            actor=None,
            action="UPLOAD",
        )


def test_store_uploaded_file_uses_candidate_naming_convention():
    """Vérifie que la clé R2 suit le format {nom}_{prenom}_{cin}/{nom_fichier}."""
    fake_file = _FakeUploadedFile("ZzzzaaZr_ReleveDeNoteInformatiqueA1.pdf", b"%PDF-1.4 test", "application/pdf")
    fake_storage = MagicMock()
    fake_profile = SimpleNamespace(nom="Zzzzaa", prenom="zr", cin="12305911", pubkey="cand_123")

    with patch("src.apps.documents.services.document_service.assert_upload_allowed"):
        result = DocumentService.store_uploaded_file(fake_file, fake_profile, fake_storage)

    fake_storage.upload.assert_called_once()
    uploaded_content, uploaded_key = fake_storage.upload.call_args.args
    assert uploaded_key == "Zzzzaa_zr_12305911/ZzzzaaZr_ReleveDeNoteInformatiqueA1.pdf"
    assert result["storage_key"] == "Zzzzaa_zr_12305911/ZzzzaaZr_ReleveDeNoteInformatiqueA1.pdf"


def test_normalize_name_segment_handles_accents_and_special_chars():
    """Vérifie la slugification/normalisation (accents, espaces, tirets, ponctuation)."""
    from src.apps.documents.services.document_service import normalize_name_segment

    assert normalize_name_segment("Éléonore") == "Eleonore"
    assert normalize_name_segment("Ben Ali") == "BenAli"
    assert normalize_name_segment("Jean-Luc") == "Jean-Luc"
    assert normalize_name_segment("O'Connor") == "OConnor"
    assert normalize_name_segment("12305911") == "12305911"


def test_homonyms_with_different_cin_have_distinct_storage_keys():
    """Vérifie que deux candidats homonymes avec des CIN différents ont des dossiers R2 distincts."""
    fake_file = _FakeUploadedFile("releve.pdf", b"%PDF-1.4 test", "application/pdf")
    fake_storage = MagicMock()

    candidate_a = SimpleNamespace(nom="Trabelsi", prenom="Ahmed", cin="11111111")
    candidate_b = SimpleNamespace(nom="Trabelsi", prenom="Ahmed", cin="22222222")

    with patch("src.apps.documents.services.document_service.assert_upload_allowed"):
        res_a = DocumentService.store_uploaded_file(fake_file, candidate_a, fake_storage)
        res_b = DocumentService.store_uploaded_file(fake_file, candidate_b, fake_storage)

    assert res_a["storage_key"] == "Trabelsi_Ahmed_11111111/releve.pdf"
    assert res_b["storage_key"] == "Trabelsi_Ahmed_22222222/releve.pdf"
    assert res_a["storage_key"] != res_b["storage_key"]


