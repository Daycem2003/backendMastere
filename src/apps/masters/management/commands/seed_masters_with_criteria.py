import uuid
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.db import transaction

from src.apps.candidate_profile.models import TypeLicence
from src.apps.coordinator.models import Coordinateur
from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.models import EligibilityCriteria
from src.apps.masters.models import Master, MasterStatus
from src.apps.users.models import User


class Command(BaseCommand):
    help = "Seed 4 test Masters with eligibility criteria (average >= 11, nationality = Tunisienne)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Début du seeding des 4 Masters de test..."))

        # 1. Vérifier ou créer le coordinateur
        coordinateur = Coordinateur.objects.filter(deleted_at__isnull=True).first()
        if not coordinateur:
            user, _ = User.objects.get_or_create(
                email="coordinateur@issat.rnu.tn",
                defaults={
                    "pubkey": f"usr_{uuid.uuid4().hex[:24]}",
                    "password_hash": "pbkdf2_sha256$mock",
                    "is_active": True,
                },
            )
            coordinateur = Coordinateur.objects.create(
                pubkey=f"coord_{uuid.uuid4().hex[:24]}",
                user=user,
                nom="Dr. Coordinateur Général",
                email="coordinateur@issat.rnu.tn",
            )

        # 2. Récupérer ou créer les TypeLicence correspondants
        licences_definitions = [
            ("informatique", "Licence Informatique"),
            ("mathematiques", "Licence Mathématiques"),
            ("physique", "Licence Physique"),
            ("chimie", "Licence Chimie"),
        ]
        type_licences = {}
        for key, intitule in licences_definitions:
            tl = TypeLicence.objects.filter(intitule__icontains=key).first()
            if not tl:
                tl = TypeLicence.objects.create(
                    pubkey=f"licence_{uuid.uuid4().hex[:20]}",
                    intitule=intitule,
                )
            type_licences[key] = tl

        # 3. Définition des 4 Masters
        now = datetime.now(timezone.utc)
        date_debut = datetime(now.year, 1, 1, tzinfo=timezone.utc)
        date_fin = datetime(now.year + 1, 12, 31, tzinfo=timezone.utc)

        masters_data = [
            {
                "pubkey": "mst_info_genie_logiciel_001",
                "nom": "Master Professionnel en Génie Logiciel & Systèmes Décisionnels",
                "universite": "Université de Sousse",
                "ville": "Sousse",
                "domaine": "Sciences et Technologies",
                "discipline": "Informatique",
                "specialite": "Génie Logiciel",
                "nombre_places": 25,
                "licence_key": "informatique",
            },
            {
                "pubkey": "mst_math_recherche_fond_002",
                "nom": "Master de Recherche en Mathématiques Fondamentales & Appliquées",
                "universite": "Université de Monastir",
                "ville": "Monastir",
                "domaine": "Sciences Fondamentales",
                "discipline": "Mathématiques",
                "specialite": "Modélisation & Analyse",
                "nombre_places": 20,
                "licence_key": "mathematiques",
            },
            {
                "pubkey": "mst_phys_energies_renouv_003",
                "nom": "Master Professionnel en Énergies Renouvelables & Matériaux Avancés",
                "universite": "Université de Tunis El Manar",
                "ville": "Tunis",
                "domaine": "Sciences Appliquées",
                "discipline": "Physique",
                "specialite": "Énergies & Nanomatériaux",
                "nombre_places": 30,
                "licence_key": "physique",
            },
            {
                "pubkey": "mst_chim_analytique_qualite_004",
                "nom": "Master Professionnel en Chimie Analytique & Contrôle Qualité",
                "universite": "Université de Carthage",
                "ville": "Carthage",
                "domaine": "Sciences Chimiques",
                "discipline": "Chimie",
                "specialite": "Analyses Physico-Chimiques",
                "nombre_places": 25,
                "licence_key": "chimie",
            },
        ]

        # 4. Création des Masters et rattachement des critères
        avg_rule = RuleValueData(
            value_type=ValueType.NUMERIC,
            operator=Operator.GTE,
            value=11.0,
        )
        nat_rule = RuleValueData(
            value_type=ValueType.STRING,
            operator=Operator.EQ,
            value="Tunisienne",
        )

        for m_data in masters_data:
            master, created = Master.objects.update_or_create(
                pubkey=m_data["pubkey"],
                defaults={
                    "nom": m_data["nom"],
                    "universite": m_data["universite"],
                    "ville": m_data["ville"],
                    "domaine": m_data["domaine"],
                    "discipline": m_data["discipline"],
                    "specialite": m_data["specialite"],
                    "nombre_places": m_data["nombre_places"],
                    "date_debut": date_debut,
                    "date_fin": date_fin,
                    "statut": MasterStatus.OUVERT,
                    "coordinateur": coordinateur,
                },
            )

            # Lier TypeLicence acceptée
            tl = type_licences.get(m_data["licence_key"])
            if tl:
                master.type_licences_acceptees.set([tl])

            # Supprimer et recréer les critères d'éligibilité pour idempotence
            EligibilityCriteria.objects.filter(master=master).delete()

            EligibilityCriteria.objects.create(
                pubkey=f"elgc_{uuid.uuid4().hex[:24]}",
                master=master,
                criterion="average",
                valeur=avg_rule.to_json(),
                obligatoire=True,
            )

            EligibilityCriteria.objects.create(
                pubkey=f"elgc_{uuid.uuid4().hex[:24]}",
                master=master,
                criterion="nationality",
                valeur=nat_rule.to_json(),
                obligatoire=True,
            )

            action = "Cree" if created else "Mis a jour"
            self.stdout.write(self.style.SUCCESS(f"[OK] {action} : {master.nom} (ID: {master.pubkey})"))

        self.stdout.write(self.style.SUCCESS("\nSeeding termine avec succes pour les 4 Masters !"))
