"""
C'est la liste des rôles système seedés dans `AUTH_ROLES`; `MST_USERS.role`
reste un champ legacy d'identité et n'est pas une source d'autorisation.
prisma/schema.prisma. Ils servent de rôles "système" seedés automatiquement
au démarrage (voir services/role_service.py::seed_default_roles) et ne
peuvent pas être supprimés via l'API (voir Role.isSystem).

Des rôles additionnels, custom, peuvent être créés dynamiquement en base par
un ADMIN (ex: "MASTER_REVIEWER") sans toucher à ce fichier ni à l'enum.
"""

CANDIDATE = "CANDIDATE"
COORDINATOR = "COORDINATOR"
ADMIN = "ADMIN"

BASE_ROLES: list[str] = [CANDIDATE, COORDINATOR, ADMIN]

BASE_ROLE_LABELS: dict[str, str] = {
    CANDIDATE: "Candidat",
    COORDINATOR: "Coordinateur",
    ADMIN: "Administrateur",
}
