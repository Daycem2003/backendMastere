from datetime import timedelta
import secrets
from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from src.apps.authorization.domain.permissions import PERMISSION_CATALOG
from src.apps.authorization.models import Permission, Role, UserRole
from src.apps.candidate_profile.models import CandidateProfile, TypeLicence
from src.apps.coordinator.models import Coordinateur
from src.apps.masters.models import Master
from src.apps.eligibility.models import EligibilityCriteria
from src.apps.users.models import User


class Command(BaseCommand):
    help = "Seed database with initial data for development and testing"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting database seed...")

        # ==============================================================
        # 1. PERMISSIONS
        # ==============================================================

        self.stdout.write("Creating permissions...")

        permissions = {}

        for definition in PERMISSION_CATALOG:
            permission, created = Permission.objects.get_or_create(
                code=definition.code,
                defaults={
                    "pubkey": "perm_" + secrets.token_urlsafe(16),
                    "resource": definition.resource,
                    "action": definition.action,
                    "description": definition.description,
                },
            )

            permissions[definition.code] = permission

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created permission: {definition.code}"
                    )
                )

        # ==============================================================
        # 2. ROLES
        # ==============================================================

        self.stdout.write("Creating roles...")

        roles_data = [
            {
                "code": "ADMIN",
                "name": "Administrateur",
                "description": "Administrateur de la plateforme",
            },
            {
                "code": "COORDINATOR",
                "name": "Coordinateur",
                "description": "Coordinateur des masters et candidatures",
            },
            {
                "code": "CANDIDATE",
                "name": "Candidat",
                "description": "Candidat à un master",
            },
        ]

        roles = {}

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data["code"],
                defaults={
                    "pubkey": "role_" + secrets.token_urlsafe(16),
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "is_system": True,
                },
            )

            roles[role_data["code"]] = role

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created role: {role_data['code']}"
                    )
                )

        # ==============================================================
        # 3. ROLE → PERMISSIONS
        # ==============================================================

        self.stdout.write("Assigning permissions to roles...")

        admin_permissions = {
            definition.code for definition in PERMISSION_CATALOG
        }

        coordinator_permissions = {
            "master:create",
            "master:update",
            "master:delete",
            "master:publish",
            "master:view",
            "master:view_draft",
            "application:view_all",
            "application:review",
            "candidate_profile:view_all",
        }

        candidate_permissions = {
            "master:view",
            "application:create",
            "application:view_own",
            "candidate_profile:view_own",
            "candidate_profile:update_own",
        }

        role_permissions = {
            "ADMIN": admin_permissions,
            "COORDINATOR": coordinator_permissions,
            "CANDIDATE": candidate_permissions,
        }

        for role_code, permission_codes in role_permissions.items():
            role = roles[role_code]

            for permission_code in permission_codes:
                permission = permissions.get(permission_code)

                if permission is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Permission not found: {permission_code}"
                        )
                    )
                    continue

                # Compatible avec le modèle RolePermission.
                from src.apps.authorization.models import RolePermission

                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )

        # ==============================================================
        # 4. LICENCE TYPES
        # ==============================================================

        self.stdout.write("Creating licence types...")

        licences_data = [
            {
                "intitule": "Licence Informatique",
                "domaine": "Sciences et Technologies",
            },
            {
                "intitule": "Licence Mathématiques",
                "domaine": "Sciences et Technologies",
            },
            {
                "intitule": "Licence Physique",
                "domaine": "Sciences et Technologies",
            },
            {
                "intitule": "Licence Chimie",
                "domaine": "Sciences et Technologies",
            },
        ]

        licences = {}

        for licence_data in licences_data:
            licence, created = TypeLicence.objects.get_or_create(
                intitule=licence_data["intitule"],
                defaults={
                    "pubkey": "licence_" + secrets.token_urlsafe(16),
                    "domaine": licence_data["domaine"],
                    "est_eligible": True,
                },
            )

            licences[licence_data["intitule"]] = licence

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created licence: {licence_data['intitule']}"
                    )
                )

        # ==============================================================
        # 5. TEST PASSWORD
        # ==============================================================

        test_password = make_password("Test1234!")

        # ==============================================================
        # 6. COORDINATOR USER
        # ==============================================================

        self.stdout.write("Creating coordinator user...")

        coord_user, created = User.objects.get_or_create(
            email="coordinateur@example.com",
            defaults={
                "pubkey": "coord_" + secrets.token_urlsafe(16),
                "password": test_password,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "  Created user: coordinateur@example.com"
                )
            )

        coordinateur, profile_created = Coordinateur.objects.get_or_create(
            user=coord_user,
            defaults={
                "pubkey": "coord_prof_" + secrets.token_urlsafe(12),
                "nom": "Ahmed Ben Ali",
                "email": "coordinateur@example.com",
            },
        )

        if profile_created:
            self.stdout.write(
                self.style.SUCCESS(
                    "  Created coordinator profile"
                )
            )

        # ==============================================================
        # 7. CANDIDATE USER
        # ==============================================================

        self.stdout.write("Creating candidate user...")

        candidate_user, created = User.objects.get_or_create(
            email="candidate@example.com",
            defaults={
                "pubkey": "cand_" + secrets.token_urlsafe(16),
                "password": test_password,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "  Created user: candidate@example.com"
                )
            )

        candidate_profile, profile_created = (
            CandidateProfile.objects.get_or_create(
                user=candidate_user,
                defaults={
                    "pubkey": "candprof_" + secrets.token_urlsafe(12),
                    "nom": "Amine",
                    "prenom": "Ben Salah",
                    "cin": "12345678",
                    "email": "amine@example.com",
                    "telephone": "+216 98 765 432",
                    "ville": "Tunis",
                    "annee_naissance": 1999,
                    "statut": "EN_ATTENTE",
                },
            )
        )

        if profile_created:
            self.stdout.write(
                self.style.SUCCESS(
                    "  Created candidate profile"
                )
            )

        # ==============================================================
        # 8. ADMIN USER
        # ==============================================================

        self.stdout.write("Creating administrator user...")

        admin_user, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "pubkey": "admin_" + secrets.token_urlsafe(16),
                "password": test_password,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "  Created user: admin@example.com"
                )
            )

        # ==============================================================
        # 9. USER → ROLE
        # ==============================================================

        self.stdout.write("Assigning roles to users...")

        assignments = [
            (admin_user, roles["ADMIN"]),
            (coord_user, roles["COORDINATOR"]),
            (candidate_user, roles["CANDIDATE"]),
        ]

        for user, role in assignments:
            UserRole.objects.update_or_create(
                user=user,
                defaults={
                    "role": role,
                    "assigned_by": None,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  {user.email} -> {role.code}"
                )
            )

        # ==============================================================
        # 10. MASTERS
        # ==============================================================

        self.stdout.write("Creating masters...")

        masters_data = [
            {
                "nom": "Master Informatique Fondamentale",
                "universite": "Université de Tunis El Manar",
                "ville": "Tunis",
                "domaine": "Informatique",
                "discipline": "Informatique Fondamentale",
                "nombre_places": 30,
                "accepted_licences": [
                    "Licence Informatique",
                    "Licence Mathématiques",
                ],
            },
            {
                "nom": "Master Mathématiques Appliquées",
                "universite": "Université de Sfax",
                "ville": "Sfax",
                "domaine": "Mathématiques",
                "discipline": "Mathématiques Appliquées",
                "nombre_places": 25,
                "accepted_licences": [
                    "Licence Mathématiques",
                    "Licence Informatique",
                ],
            },
            {
                "nom": "Master Physique Quantique",
                "universite": "Université de Sousse",
                "ville": "Sousse",
                "domaine": "Physique",
                "discipline": "Physique Quantique",
                "nombre_places": 20,
                "accepted_licences": [
                    "Licence Physique",
                    "Licence Mathématiques",
                ],
            },
            {
                "nom": "Master Chimie Industrielle",
                "universite": "Université de Monastir",
                "ville": "Monastir",
                "domaine": "Chimie",
                "discipline": "Chimie Industrielle",
                "nombre_places": 28,
                "accepted_licences": [
                    "Licence Chimie",
                    "Licence Physique",
                ],
            },
        ]

        for master_data in masters_data:
            master, created = Master.objects.get_or_create(
                nom=master_data["nom"],
                defaults={
                    "pubkey": "master_" + secrets.token_urlsafe(12),
                    "universite": master_data["universite"],
                    "ville": master_data["ville"],
                    "domaine": master_data["domaine"],
                    "discipline": master_data["discipline"],
                    "nombre_places": master_data["nombre_places"],
                    "coordinateur": coordinateur,
                    "date_debut": now() + timedelta(days=30),
                    "date_fin": now() + timedelta(days=90),
                    "statut": "OUVERT",
                },
            )

            for licence_name in master_data["accepted_licences"]:
                licence = licences.get(licence_name)

                if licence:
                    master.type_licences_acceptees.add(licence)

            rule_value = RuleValueData(
                value_type=ValueType.NUMERIC,
                operator=Operator.GTE,
                value=12,
            )

            EligibilityCriteria.objects.get_or_create(
                master=master,
                criterion="average",
                defaults={
                    "pubkey": "crit_" + secrets.token_urlsafe(12),
                    "valeur": rule_value.to_json(),
                    "obligatoire": True,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created master: {master_data['nom']}"
                    )
                )

        # ==============================================================
        # 11. SUMMARY
        # ==============================================================

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Database seeded successfully."
            )
        )

        self.stdout.write("")
        self.stdout.write("Test accounts:")
        self.stdout.write(
            "  Candidate     : candidate@example.com"
        )
        self.stdout.write(
            "  Coordinator   : coordinateur@example.com"
        )
        self.stdout.write(
            "  Administrator : admin@example.com"
        )

        self.stdout.write("")
        self.stdout.write("Test password:")
        self.stdout.write("  Test1234!")

        self.stdout.write("")
        self.stdout.write("RBAC:")
        self.stdout.write(
            "  candidate@example.com    -> CANDIDATE"
        )
        self.stdout.write(
            "  coordinateur@example.com -> COORDINATOR"
        )
        self.stdout.write(
            "  admin@example.com        -> ADMIN"
        )