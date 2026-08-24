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

    result = DocumentService.store_uploaded_file(fake_file, "cand_pubkey_1", fake_storage)

    fake_storage.upload.assert_called_once()
    uploaded_content, uploaded_key = fake_storage.upload.call_args.args
    assert uploaded_content is fake_file
    assert uploaded_key.startswith("cand_pubkey_1/")
    assert result["mime_type"] == "application/pdf"
    assert result["file_size"] == len(b"%PDF-1.4 contenu test")
    assert len(result["checksum"]) == 64  # sha256 hex digest


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
