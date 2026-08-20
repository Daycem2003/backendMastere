"""
Table de vérité utilisée UNIQUEMENT au seed initial (services/role_service.py
::seed_default_roles). Une fois en base, les permissions réelles d'un rôle
vivent dans AUTH_ROLE_PERMISSIONS et peuvent diverger de cette table si un
ADMIN les modifie ensuite via l'API — ce fichier ne doit donc pas être
consulté à l'exécution pour vérifier une permission (voir
selectors/authorization_selector.py qui lit toujours la base).
"""

from src.apps.authorization.domain import roles as R
from src.apps.authorization.domain import permissions as P

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    R.CANDIDATE: [
        P.MASTER_VIEW,
        P.APPLICATION_CREATE,
        P.APPLICATION_VIEW_OWN,
        P.CANDIDATE_PROFILE_VIEW_OWN,
        P.CANDIDATE_PROFILE_UPDATE_OWN,
    ],
    R.COORDINATOR: [
        P.MASTER_VIEW,
        P.MASTER_VIEW_DRAFT,
        P.MASTER_CREATE,
        P.MASTER_UPDATE,
        P.MASTER_PUBLISH,
        P.APPLICATION_VIEW_ALL,
        P.APPLICATION_REVIEW,
        P.CANDIDATE_PROFILE_VIEW_ALL,
    ],
    R.ADMIN: [perm.code for perm in P.PERMISSION_CATALOG],  # accès total
}
