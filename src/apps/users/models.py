from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class User(TimestampedSoftDeleteModel):
    """Identité de l'utilisateur uniquement — l'autorisation est
    entièrement déléguée au RBAC du module `authorization`
    (`Role` / `UserRole`). Ce modèle ne représente et n'expose aucun rôle.

    NOTE SUR LA COLONNE LEGACY `role` : la colonne `role` peut encore
    exister physiquement en base, mais elle n'est pas mappée par ce modèle.
    Toute suppression éventuelle doit faire partie d'une migration explicite.

    Ce qui change ici : la colonne n'est **plus du tout mappée** dans ce
    modèle Django. Aucune ligne de code de `users` ne peut donc plus lire
    ni écrire dessus — c'est la garantie la plus forte qu'on puisse donner
    côté application sans toucher au schéma physique. Si un autre module
    (hors de ceux que j'ai audités) lit encore cette colonne via SQL brut
    ou un autre ORM, ça reste hors de mon contrôle : à vérifier de ton
    côté (voir README, section "recherche à faire").
    """

    pubkey = models.TextField(unique=True)
    email = models.TextField(unique=True)
    password = models.TextField()  # jamais exposé : voir serializers/user.py
    is_active = models.BooleanField(default=True, db_column="isActive")

    # Requis par DRF/Django pour toute classe utilisee comme request.user.
    # Ce modele n'herite pas de AbstractBaseUser/PermissionsMixin
    # (l'autorisation est deleguee au RBAC de `authorization`), donc ces
    # deux attributs ne sont pas fournis automatiquement : on les declare
    # ici en dur. Toute instance de User recuperee depuis la DB via
    # l'authentification represente forcement un utilisateur authentifie
    # et non anonyme.
    is_authenticated = True
    is_anonymous = False

    class Meta:
        managed = True
        db_table = "MST_USERS"


# --- Re-export de compatibilite ----------------------------------------
#
# `src/apps/authentication/models.py` importe `UserRole` depuis
# `src.apps.users.models`. Le modele `UserRole` (table AUTH_USER_ROLES)
# est physiquement declare dans `authorization` (FK vers
# `authorization.Role`) - pas ici. Re-export, pas redefinition, pour
# eviter un conflit Django (meme table, deux app_label). Inchange par
# cette refactorisation.
#
# Recommandation toujours valable : corriger le fichier de compatibilite
# `authentication` pour importer directement depuis
# `src.apps.authorization.models.user_role`, ce qui rendrait ce re-export
# inutile.
try:
    from src.apps.authorization.models.user_role import UserRole  # noqa: F401
except ImportError:  # pragma: no cover - depend de l'ordre de chargement des apps
    UserRole = None