"""
Format de code : "<resource>:<action>". Chaque constante ici DOIT avoir une
entrée correspondante dans PERMISSION_CATALOG (description + resource/action
séparés) pour que services/permission_service.py::seed_default_permissions
puisse peupler la table AUTH_PERMISSIONS.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    resource: str
    action: str
    description: str


# ------------------------------------------------------------------ #
# Master
# ------------------------------------------------------------------ #
MASTER_CREATE = "master:create"
MASTER_UPDATE = "master:update"
MASTER_DELETE = "master:delete"
MASTER_PUBLISH = "master:publish"
MASTER_VIEW = "master:view"
MASTER_VIEW_DRAFT = "master:view_draft"

# ------------------------------------------------------------------ #
# Application (candidature)
# ------------------------------------------------------------------ #
APPLICATION_CREATE = "application:create"
APPLICATION_VIEW_OWN = "application:view_own"
APPLICATION_VIEW_ALL = "application:view_all"
APPLICATION_REVIEW = "application:review"

# ------------------------------------------------------------------ #
# Candidate profile
# ------------------------------------------------------------------ #
CANDIDATE_PROFILE_VIEW_OWN = "candidate_profile:view_own"
CANDIDATE_PROFILE_VIEW_ALL = "candidate_profile:view_all"
CANDIDATE_PROFILE_UPDATE_OWN = "candidate_profile:update_own"

# ------------------------------------------------------------------ #
# Authorization (méta - gérer les rôles/permissions eux-mêmes)
# ------------------------------------------------------------------ #
ROLE_MANAGE = "role:manage"
PERMISSION_MANAGE = "permission:manage"
USER_ROLE_ASSIGN = "user_role:assign"


PERMISSION_CATALOG: list[PermissionDefinition] = [
    PermissionDefinition(MASTER_CREATE, "master", "create", "Créer un master"),
    PermissionDefinition(MASTER_UPDATE, "master", "update", "Modifier un master"),
    PermissionDefinition(MASTER_DELETE, "master", "delete", "Supprimer un master"),
    PermissionDefinition(MASTER_PUBLISH, "master", "publish", "Publier/ouvrir un master"),
    PermissionDefinition(MASTER_VIEW, "master", "view", "Voir les masters publiés"),
    PermissionDefinition(MASTER_VIEW_DRAFT, "master", "view_draft", "Voir les masters en brouillon"),
    PermissionDefinition(APPLICATION_CREATE, "application", "create", "Soumettre une candidature"),
    PermissionDefinition(APPLICATION_VIEW_OWN, "application", "view_own", "Voir ses propres candidatures"),
    PermissionDefinition(APPLICATION_VIEW_ALL, "application", "view_all", "Voir toutes les candidatures d'un master géré"),
    PermissionDefinition(APPLICATION_REVIEW, "application", "review", "Évaluer/statuer sur une candidature"),
    PermissionDefinition(CANDIDATE_PROFILE_VIEW_OWN, "candidate_profile", "view_own", "Voir son propre profil"),
    PermissionDefinition(CANDIDATE_PROFILE_VIEW_ALL, "candidate_profile", "view_all", "Voir tous les profils candidats"),
    PermissionDefinition(CANDIDATE_PROFILE_UPDATE_OWN, "candidate_profile", "update_own", "Modifier son propre profil"),
    PermissionDefinition(ROLE_MANAGE, "role", "manage", "Créer/modifier/supprimer des rôles"),
    PermissionDefinition(PERMISSION_MANAGE, "permission", "manage", "Créer/modifier des permissions"),
    PermissionDefinition(USER_ROLE_ASSIGN, "user_role", "assign", "Assigner ou révoquer un rôle à un utilisateur"),
]
