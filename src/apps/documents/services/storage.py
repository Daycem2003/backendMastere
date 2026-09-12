import logging
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class StorageBackend(Protocol):
    def upload(self, content, key: str) -> str: ...
    def delete(self, key: str) -> None: ...
    def signed_url(self, key: str, expires_in: int = 300) -> str: ...


class LocalStorageBackend:
    """Backend de secours pour le développement local et les tests, quand
    aucune credential R2 n'est configurée. Ne doit jamais servir en
    production — signed_url() y renvoie un chemin non signé."""

    def __init__(self, root: str):
        self.root = Path(root)

    def upload(self, content, key: str) -> str:
        destination = self.root / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            for chunk in content.chunks():
                output.write(chunk)
        return key

    def delete(self, key: str) -> None:
        path = self.root / key
        if path.exists():
            path.unlink()

    def signed_url(self, key: str, expires_in: int = 300) -> str:
        return f"/media/{key}"


class R2StorageBackend:
    """Backend S3-compatible pour Cloudflare R2, via boto3.

    Le bucket reste privé : aucune URL publique n'est jamais renvoyée.
    signed_url() génère une presigned URL temporaire (GET uniquement),
    seul moyen pour le frontend d'accéder à un fichier — les credentials
    R2 ne quittent jamais le backend.
    """

    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str, bucket_name: str, endpoint_url: str):
        import boto3
        from botocore.config import Config

        self.bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def upload(self, content, key: str) -> str:
        content.seek(0)
        extra_args = {}
        content_type = getattr(content, "content_type", None)
        if content_type:
            extra_args["ContentType"] = content_type
        self._client.upload_fileobj(content, self.bucket_name, key, ExtraArgs=extra_args or None)
        logger.info("r2_upload", extra={"key": key})
        return key

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket_name, Key=key)
        logger.info("r2_delete", extra={"key": key})

    def signed_url(self, key: str, expires_in: int = 300) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )


_storage_instance: StorageBackend | None = None


def get_default_storage() -> StorageBackend:
    """Point d'entrée unique pour obtenir le backend de stockage configuré.

    Utilise R2 dès que les 5 variables R2_* sont présentes dans les
    settings (donc en environnement réel via .env). Retombe sur le stockage
    local uniquement si l'une d'elles manque — typiquement en dev sans R2
    configuré, ou en tests. L'instance boto3 est mise en cache pour éviter
    de recréer un client à chaque appel.
    """
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    from django.conf import settings

    account_id = getattr(settings, "R2_ACCOUNT_ID", None)
    access_key_id = getattr(settings, "R2_ACCESS_KEY_ID", None)
    secret_access_key = getattr(settings, "R2_SECRET_ACCESS_KEY", None)
    bucket_name = getattr(settings, "R2_BUCKET_NAME", None)
    endpoint_url = getattr(settings, "R2_ENDPOINT_URL", None)

    if all([account_id, access_key_id, secret_access_key, bucket_name, endpoint_url]):
        _storage_instance = R2StorageBackend(
            account_id=account_id,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
        )
    else:
        logger.warning("r2_not_configured_falling_back_to_local_storage")
        root = getattr(settings, "DOCUMENTS_STORAGE_ROOT", "media/documents")
        _storage_instance = LocalStorageBackend(root)

    return _storage_instance


def reset_storage_cache() -> None:
    """Utilitaire pour les tests : force la recréation du backend au
    prochain appel de get_default_storage() (utile après avoir patché les
    settings R2_* dans un test)."""
    global _storage_instance
    _storage_instance = None