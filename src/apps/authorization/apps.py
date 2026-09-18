from django.apps import AppConfig


class AuthorizationConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "src.apps.authorization"
    label = "authorization"

    def ready(self) -> None:
        # Auto-seed du RBAC système après chaque `migrate`.
        # Remplace l'ancienne data migration 0002_seed_rbac et le lifespan
        # FastAPI (src/fastapi_app/main.py), qui sont désormais du code mort.
        from src.apps.authorization.signals.seed_rbac import connect_seed_rbac_signals

        connect_seed_rbac_signals()
