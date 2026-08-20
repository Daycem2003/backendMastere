from django.db import migrations, transaction


ROLE_SEEDS = (
    {
        "pubkey": "role_candidate",
        "code": "CANDIDATE",
        "name": "Candidat",
        "description": "Role systeme des candidats.",
    },
    {
        "pubkey": "role_coordinator",
        "code": "COORDINATOR",
        "name": "Coordinateur",
        "description": "Role systeme des coordinateurs.",
    },
    {
        "pubkey": "role_admin",
        "code": "ADMIN",
        "name": "Administrateur",
        "description": "Role systeme des administrateurs.",
    },
)

PERMISSION_SEEDS = (
    ("master:create", "master", "create", "Creer un master"),
    ("master:update", "master", "update", "Modifier un master"),
    ("master:delete", "master", "delete", "Supprimer un master"),
    ("master:publish", "master", "publish", "Publier/ouvrir un master"),
    ("master:view", "master", "view", "Voir les masters publies"),
    ("master:view_draft", "master", "view_draft", "Voir les masters en brouillon"),
    ("application:create", "application", "create", "Soumettre une candidature"),
    ("application:view_own", "application", "view_own", "Voir ses propres candidatures"),
    ("application:view_all", "application", "view_all", "Voir toutes les candidatures d'un master gere"),
    ("application:review", "application", "review", "Evaluer/statuer sur une candidature"),
    ("candidate_profile:view_own", "candidate_profile", "view_own", "Voir son propre profil"),
    ("candidate_profile:view_all", "candidate_profile", "view_all", "Voir tous les profils candidats"),
    ("candidate_profile:update_own", "candidate_profile", "update_own", "Modifier son propre profil"),
    ("role:manage", "role", "manage", "Creer/modifier/supprimer des roles"),
    ("permission:manage", "permission", "manage", "Creer/modifier des permissions"),
    ("user_role:assign", "user_role", "assign", "Assigner ou revoquer un role a un utilisateur"),
)

ROLE_PERMISSION_CODES = {
    "CANDIDATE": (
        "master:view",
        "application:create",
        "application:view_own",
        "candidate_profile:view_own",
        "candidate_profile:update_own",
    ),
    "COORDINATOR": (
        "master:view",
        "master:view_draft",
        "master:create",
        "master:update",
        "master:publish",
        "application:view_all",
        "application:review",
        "candidate_profile:view_all",
    ),
    "ADMIN": tuple(seed[0] for seed in PERMISSION_SEEDS),
}


def _get_or_create_by_code(model, code, defaults):
    existing = model.objects.filter(code=code).first()
    if existing:
        return existing, False

    pubkey = defaults["pubkey"]
    collision = model.objects.filter(pubkey=pubkey).first()
    if collision:
        raise RuntimeError(
            f"RBAC seed pubkey collision for {model._meta.db_table}: {pubkey}"
        )
    return model.objects.create(code=code, **defaults), True


def seed_rbac(apps, schema_editor):
    Role = apps.get_model("authorization", "Role")
    Permission = apps.get_model("authorization", "Permission")
    RolePermission = apps.get_model("authorization", "RolePermission")

    with transaction.atomic(using=schema_editor.connection.alias):
        roles = {}
        for seed in ROLE_SEEDS:
            role, _ = _get_or_create_by_code(
                Role,
                seed["code"],
                {
                    "pubkey": seed["pubkey"],
                    "name": seed["name"],
                    "description": seed["description"],
                    "is_system": True,
                },
            )
            roles[role.code] = role

        permissions = {}
        for code, resource, action, description in PERMISSION_SEEDS:
            permission, _ = _get_or_create_by_code(
                Permission,
                code,
                {
                    "pubkey": f"perm_{code.replace(':', '_')}",
                    "resource": resource,
                    "action": action,
                    "description": description,
                },
            )
            permissions[permission.code] = permission

        for role_code, permission_codes in ROLE_PERMISSION_CODES.items():
            role = roles[role_code]
            for permission_code in permission_codes:
                RolePermission.objects.get_or_create(
                    role_id=role.pk,
                    permission_id=permissions[permission_code].pk,
                )


def unseed_rbac(apps, schema_editor):
    Role = apps.get_model("authorization", "Role")
    Permission = apps.get_model("authorization", "Permission")
    RolePermission = apps.get_model("authorization", "RolePermission")

    seeded_role_pubkeys = [seed["pubkey"] for seed in ROLE_SEEDS]
    seeded_permission_pubkeys = [
        f"perm_{code.replace(':', '_')}" for code, *_ in PERMISSION_SEEDS
    ]

    with transaction.atomic(using=schema_editor.connection.alias):
        seeded_roles = Role.objects.filter(pubkey__in=seeded_role_pubkeys)
        seeded_permissions = Permission.objects.filter(pubkey__in=seeded_permission_pubkeys)
        RolePermission.objects.filter(
            role_id__in=seeded_roles.values_list("pk", flat=True),
            permission_id__in=seeded_permissions.values_list("pk", flat=True),
        ).delete()
        seeded_roles.delete()
        seeded_permissions.delete()


class Migration(migrations.Migration):
    dependencies = [("authorization", "0001_initial")]

    operations = [migrations.RunPython(seed_rbac, unseed_rbac)]
