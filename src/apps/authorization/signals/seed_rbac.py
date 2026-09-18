"""
Auto-seed des rôles/permissions système au moment de `migrate`.

Ceci remplace deux mécanismes désormais obsolètes et qui ne fonctionnaient
plus:
    - l'ancienne data migration `0002_seed_rbac` (supprimée dans 05cfb63);
    - le lifespan FastAPI de `src/fastapi_app/main.py` (code mort: rien ne
      référence plus cette app FastAPI, et fastapi n'est plus une dépendance).

Le handler est connecté sur le signal Django `post_migrate` via
`AuthorizationConfig.ready()`. Il est idempotent (get_or_create /
bulk_create(ignore_conflicts=True)) et peut donc tourner à chaque `migrate`.
"""

import logging

from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

# dispatch_uid stable: empêche une double connexion si ready() est appelé
# plusieurs fois.
_DISPATCH_UID = "authorization.seed_default_rbac"


def seed_default_rbac(
    sender=None,
    *args,
    app_label: str | None = None,
    app_config=None,
    **kwargs,
) -> None:
    """Seed l'état RBAC système après la migration de l'app `authorization`.

    Ordre important: les permissions sont créées AVANT les rôles, car
    `RoleService._seed_default_roles` link les RolePermission vers des
    Permission déjà présentes (filtrées sur code).
    """
    # Récupérer l'app_label depuis le signal; sinon le déduire de l'AppConfig
    # sender (le post_migrate peut être émis sans app_label dans certains
    # contextes, ex. pytest-django).
    if app_label is None and app_config is not None:
        app_label = getattr(app_config, "label", None)

    # Un seul appel par `migrate`: le signal est émis pour chaque app_label,
    # on ne seed qu'une fois l'app authorization (dont les tables
    # Permission/Role/RolePermission viennent d'être créées par 0001).
    if app_label != "authorization":
        return

    # Import paresseux: évite tout couplage d'import au moment de
    # l'initialisation des applications (ready()).
    from src.apps.authorization.services.permission_service import PermissionService
    from src.apps.authorization.services.role_service import RoleService

    # Points d'entrée synchrones (non-async): post_migrate s'exécute dans un
    # contexte de migration synchrone, on contourne donc les wrappers
    # sync_to_async. Les méthodes internes sont déjà @transaction.atomic,
    # ce qui est compatible avec la transaction de migration en cours.
    PermissionService._seed_default_permissions()
    RoleService._seed_default_roles()

    logger.info("RBAC système initialisé (rôles + permissions par défaut).")


def connect_seed_rbac_signals() -> None:
    """À appeler depuis `AuthorizationConfig.ready()`."""
    post_migrate.connect(
        seed_default_rbac,
        dispatch_uid=_DISPATCH_UID,
    )
