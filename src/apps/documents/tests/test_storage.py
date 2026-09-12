# src/apps/documents/tests/test_storage.py
from unittest.mock import MagicMock, patch

import pytest

from src.apps.documents.services.storage import (
    LocalStorageBackend,
    R2StorageBackend,
    get_default_storage,
    reset_storage_cache,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_storage_cache()
    yield
    reset_storage_cache()


def test_falls_back_to_local_storage_when_r2_not_configured(settings):
    settings.R2_ACCOUNT_ID = None
    settings.R2_ACCESS_KEY_ID = None
    settings.R2_SECRET_ACCESS_KEY = None
    settings.R2_BUCKET_NAME = None
    settings.R2_ENDPOINT_URL = None

    backend = get_default_storage()
    assert isinstance(backend, LocalStorageBackend)


def test_uses_r2_when_fully_configured(settings):
    settings.R2_ACCOUNT_ID = "acc"
    settings.R2_ACCESS_KEY_ID = "key"
    settings.R2_SECRET_ACCESS_KEY = "secret"
    settings.R2_BUCKET_NAME = "bucket"
    settings.R2_ENDPOINT_URL = "https://acc.r2.cloudflarestorage.com"

    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        backend = get_default_storage()

    assert isinstance(backend, R2StorageBackend)
    mock_boto_client.assert_called_once()


def test_r2_signed_url_never_exposes_credentials():
    with patch("boto3.client") as mock_boto_client:
        client = MagicMock()
        client.generate_presigned_url.return_value = "https://signed.example/x?sig=..."
        mock_boto_client.return_value = client

        backend = R2StorageBackend(
            account_id="acc",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="bucket",
            endpoint_url="https://acc.r2.cloudflarestorage.com",
        )
        url = backend.signed_url("some/key.pdf", expires_in=120)

    assert url == "https://signed.example/x?sig=..."
    client.generate_presigned_url.assert_called_once_with(
        "get_object", Params={"Bucket": "bucket", "Key": "some/key.pdf"}, ExpiresIn=120
    )