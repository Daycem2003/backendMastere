import logging
from datetime import datetime, timezone

from django.conf import settings
from django.db import models, transaction

from src.apps.documents.exceptions.document_exceptions import FileTooLarge, StorageQuotaExceeded
from src.apps.documents.models import DocumentVersion, R2OperationCounter
from src.apps.documents.services.storage import StorageBackend, get_default_storage

logger = logging.getLogger(__name__)


def _cfg(name: str, default):
    """Lit un réglage R2_* depuis Django settings (donc depuis .env via
    django-environ/decouple), avec un défaut de secours si absent."""
    return getattr(settings, name, default)


# --- Limites brutes (plan gratuit Cloudflare R2), configurables via .env ---
MAX_STORAGE_BYTES = _cfg("R2_MAX_STORAGE_GB", 10) * 1024 * 1024 * 1024
MAX_CLASS_A_OPS = _cfg("R2_MAX_CLASS_A", 1_000_000)
MAX_CLASS_B_OPS = _cfg("R2_MAX_CLASS_B", 10_000_000)
MAX_FILE_SIZE_BYTES = _cfg("R2_MAX_FILE_SIZE_MB", 5) * 1024 * 1024

# --- Seuils en % pour chaque ressource ---
STORAGE_WARNING_PCT = _cfg("R2_STORAGE_WARNING_PERCENT", 70)
STORAGE_CRITICAL_PCT = _cfg("R2_STORAGE_CRITICAL_PERCENT", 85)
STORAGE_BLOCK_PCT = _cfg("R2_STORAGE_BLOCK_PERCENT", 95)

CLASS_A_WARNING_PCT = _cfg("R2_CLASS_A_WARNING_PERCENT", 70)
CLASS_A_CRITICAL_PCT = _cfg("R2_CLASS_A_CRITICAL_PERCENT", 85)
CLASS_A_BLOCK_PCT = _cfg("R2_CLASS_A_BLOCK_PERCENT", 95)

CLASS_B_WARNING_PCT = _cfg("R2_CLASS_B_WARNING_PERCENT", 70)
CLASS_B_CRITICAL_PCT = _cfg("R2_CLASS_B_CRITICAL_PERCENT", 85)
CLASS_B_BLOCK_PCT = _cfg("R2_CLASS_B_BLOCK_PERCENT", 95)


def _current_period() -> str:
    """Période de facturation R2 = mois calendaire UTC, format 'YYYY-MM'."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _check_thresholds(resource: str, used: float, limit: float, warning_pct: float, critical_pct: float, block_pct: float) -> None:
    """Calcule le % d'utilisation d'une ressource et log/lève selon le
    palier atteint. Ne lève StorageQuotaExceeded qu'au palier BLOCK — les
    paliers WARNING et CRITICAL ne font que logger, pour permettre une
    alerte/monitoring sans bloquer le service tant que ce n'est pas
    critique."""
    ratio_pct = (used / limit * 100) if limit else 0

    if ratio_pct >= block_pct:
        logger.error(
            "r2_budget_block",
            extra={"resource": resource, "used": used, "limit": limit, "ratio_pct": round(ratio_pct, 2)},
        )
        raise StorageQuotaExceeded()
    elif ratio_pct >= critical_pct:
        logger.warning(
            "r2_budget_critical",
            extra={"resource": resource, "used": used, "limit": limit, "ratio_pct": round(ratio_pct, 2)},
        )
    elif ratio_pct >= warning_pct:
        logger.info(
            "r2_budget_warning",
            extra={"resource": resource, "used": used, "limit": limit, "ratio_pct": round(ratio_pct, 2)},
        )


@transaction.atomic
def assert_upload_allowed(file_size: int) -> None:
    """À appeler AVANT tout upload réel vers R2 (et avant le hash coûteux
    du fichier — voir DocumentService.store_uploaded_file).

    Vérifie, dans l'ordre :
    1. La taille du fichier lui-même (R2_MAX_FILE_SIZE_MB) — rejet
       immédiat, indépendant des compteurs globaux.
    2. Le budget de stockage total (fichiers actifs, non soft-deleted)
       avec ce nouvel upload inclus.
    3. Le budget d'opérations Class A du mois courant (un upload = 1 PUT
       = 1 opération Class A).

    select_for_update() sur le compteur du mois sérialise les uploads
    concurrents pour éviter un dépassement en race condition.
    """
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(
            "r2_file_too_large",
            extra={"file_size": file_size, "max_allowed": MAX_FILE_SIZE_BYTES},
        )
        raise FileTooLarge()

    total_stored = (
        DocumentVersion.objects.filter(deleted_at__isnull=True)
        .aggregate(total=models.Sum("file_size"))
        .get("total") or 0
    )
    _check_thresholds(
        "storage", total_stored + file_size, MAX_STORAGE_BYTES,
        STORAGE_WARNING_PCT, STORAGE_CRITICAL_PCT, STORAGE_BLOCK_PCT,
    )

    counter, _ = R2OperationCounter.objects.select_for_update().get_or_create(period=_current_period())
    _check_thresholds(
        "class_a", counter.class_a_count + 1, MAX_CLASS_A_OPS,
        CLASS_A_WARNING_PCT, CLASS_A_CRITICAL_PCT, CLASS_A_BLOCK_PCT,
    )

    counter.class_a_count += 1
    counter.save(update_fields=["class_a_count"])


def _record_class_b_operation() -> None:
    """Incrémente le compteur d'opérations Class B (lecture/download) et
    vérifie les seuils. Best-effort et non bloquant en cas d'erreur de
    tracking : une signed_url déjà autorisée par les permissions
    applicatives n'échoue jamais à cause d'un souci de comptage — mais le
    palier BLOCK lève quand même StorageQuotaExceeded si le budget Class B
    est réellement dépassé, pour éviter une facturation surprise."""
    try:
        with transaction.atomic():
            counter, _ = R2OperationCounter.objects.select_for_update().get_or_create(period=_current_period())
            counter.class_b_count += 1
            counter.save(update_fields=["class_b_count"])
            _check_thresholds(
                "class_b", counter.class_b_count, MAX_CLASS_B_OPS,
                CLASS_B_WARNING_PCT, CLASS_B_CRITICAL_PCT, CLASS_B_BLOCK_PCT,
            )
    except StorageQuotaExceeded:
        raise
    except Exception:
        logger.exception("r2_class_b_tracking_failed")


class _BudgetedStorageWrapper:
    """Enveloppe transparente autour d'un StorageBackend : délègue tout,
    mais trace chaque génération de signed_url comme une opération Class B
    potentielle (le front va probablement effectuer le GET juste après)."""

    def __init__(self, inner: StorageBackend):
        self._inner = inner

    def upload(self, content, key: str) -> str:
        return self._inner.upload(content, key)

    def delete(self, key: str) -> None:
        self._inner.delete(key)

    def signed_url(self, key: str, expires_in: int = 300) -> str:
        _record_class_b_operation()
        return self._inner.signed_url(key, expires_in=expires_in)


def get_budgeted_storage() -> StorageBackend:
    """Point d'entrée utilisé par les vues (context={'storage': ...}) et
    DocumentService.store_uploaded_file. Toujours utiliser cette fonction
    plutôt que get_default_storage() directement dans le code applicatif,
    pour garder le tracking Class B centralisé."""
    return _BudgetedStorageWrapper(get_default_storage())