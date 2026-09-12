import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.apps.applications.dto.application import SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import (
    AlreadyApplied,
    CandidateProfileRequired,
    NotEligible,
)
from src.apps.applications.models import Application, ApplicationStatus
from src.apps.applications.services.application_service import ApplicationService
from src.apps.candidate_profile.models import CandidateProfile, Diplome, LicenceYear, TypeLicence
from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.models import EligibilityCriteria
from django.utils import timezone
from src.apps.coordinator.models import Coordinateur
from src.apps.masters.models import Master, MasterStatus
from src.apps.users.models import User


@pytest.fixture
def type_licence_info(db):
    return TypeLicence.objects.create(pubkey="lic_info_01", intitule="Informatique")


@pytest.fixture
def master_with_criteria(db, type_licence_info):
    user = User.objects.create(pubkey="usr_coord_test", email="coord@test.tn", password="password")
    coord = Coordinateur.objects.create(pubkey="coord_test_pk", user=user, nom="Coordinateur Test", email="coord@test.tn")
    now = timezone.now()

    master = Master.objects.create(
        pubkey="mst_test_01",
        nom="Mastère Test Informatique",
        universite="Université de Test",
        ville="Tunis",
        domaine="Informatique",
        discipline="Informatique",
        specialite="IA",
        nombre_places=10,
        date_debut=now - timezone.timedelta(days=10),
        date_fin=now + timezone.timedelta(days=30),
        statut=MasterStatus.OUVERT,
        coordinateur=coord,
    )
    master.type_licences_acceptees.add(type_licence_info)

    # Critère 1: moyenne >= 11.0
    EligibilityCriteria.objects.create(
        pubkey="ec_avg_01",
        master=master,
        criterion="average",
        obligatoire=True,
        rule_value=RuleValueData(
            value_type=ValueType.NUMERIC,
            operator=Operator.GTE,
            value=11.0,
        ),
    )
    # Critère 2: nationalité = Tunisienne
    EligibilityCriteria.objects.create(
        pubkey="ec_nat_01",
        master=master,
        criterion="nationality",
        obligatoire=True,
        rule_value=RuleValueData(
            value_type=ValueType.STRING,
            operator=Operator.EQ,
            value="Tunisienne",
        ),
    )
    return master


@pytest.mark.django_db
def test_submit_fails_when_profile_not_valide(master_with_criteria, type_licence_info):
    profile = CandidateProfile.objects.create(
        pubkey="cand_pending",
        nom="Ben Ali",
        prenom="Sami",
        cin="12345678",
        email="sami@test.tn",
        telephone="12345678",
        ville="Tunis",
        nationalite="Tunisienne",
        annee_naissance=2000,
        statut="EN_ATTENTE",
    )
    with pytest.raises(CandidateProfileRequired):
        ApplicationService.submit(profile, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))


@pytest.mark.django_db
def test_submit_fails_when_average_below_minimum(master_with_criteria, type_licence_info):
    profile = CandidateProfile.objects.create(
        pubkey="cand_low_avg",
        nom="Trabelsi",
        prenom="Amine",
        cin="22345678",
        email="amine@test.tn",
        telephone="22345678",
        ville="Sousse",
        nationalite="Tunisienne",
        annee_naissance=2000,
        statut="VALIDE",
    )
    diplome = Diplome.objects.create(
        pubkey="dip_low_avg",
        candidate_profile=profile,
        type_licence=type_licence_info,
        universite="ISITCom",
        annee_obtention="2024",
    )
    # 3 années avec moyennes 9.0, 10.0, 10.0 -> Moyenne = 9.67 < 11.0
    LicenceYear.objects.create(pubkey="ly_low_1", candidate_profile=profile, type_licence=type_licence_info, annee=1, annee_universitaire="2021/2022", moyenne=9.0)
    LicenceYear.objects.create(pubkey="ly_low_2", candidate_profile=profile, type_licence=type_licence_info, annee=2, annee_universitaire="2022/2023", moyenne=10.0)
    LicenceYear.objects.create(pubkey="ly_low_3", candidate_profile=profile, type_licence=type_licence_info, annee=3, annee_universitaire="2023/2024", moyenne=10.0)

    with pytest.raises(NotEligible) as exc_info:
        ApplicationService.submit(profile, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))

    assert "Moyenne minimale de Licence requise" in str(exc_info.value.detail)


@pytest.mark.django_db
def test_submit_fails_when_nationality_mismatch(master_with_criteria, type_licence_info):
    profile = CandidateProfile.objects.create(
        pubkey="cand_foreign",
        nom="Dupont",
        prenom="Pierre",
        cin="32345678",
        email="pierre@test.fr",
        telephone="32345678",
        ville="Paris",
        nationalite="Française",
        annee_naissance=1999,
        statut="VALIDE",
    )
    Diplome.objects.create(
        pubkey="dip_foreign",
        candidate_profile=profile,
        type_licence=type_licence_info,
        universite="Sorbonne",
        annee_obtention="2024",
    )
    LicenceYear.objects.create(pubkey="ly_for_1", candidate_profile=profile, type_licence=type_licence_info, annee=1, annee_universitaire="2021/2022", moyenne=14.0)
    LicenceYear.objects.create(pubkey="ly_for_2", candidate_profile=profile, type_licence=type_licence_info, annee=2, annee_universitaire="2022/2023", moyenne=14.0)
    LicenceYear.objects.create(pubkey="ly_for_3", candidate_profile=profile, type_licence=type_licence_info, annee=3, annee_universitaire="2023/2024", moyenne=14.0)

    with pytest.raises(NotEligible) as exc_info:
        ApplicationService.submit(profile, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))

    assert "Nationalité requise" in str(exc_info.value.detail)


@pytest.mark.django_db
def test_submit_succeeds_and_recalculates_ranks(master_with_criteria, type_licence_info):
    # Candidat 1 avec moyenne 12.0 -> Score = 12.0
    cand1 = CandidateProfile.objects.create(
        pubkey="cand_1_rank",
        nom="Gharbi",
        prenom="Yassine",
        cin="42345678",
        email="yassine@test.tn",
        telephone="42345678",
        ville="Monastir",
        nationalite="Tunisienne",
        annee_naissance=2001,
        statut="VALIDE",
    )
    Diplome.objects.create(pubkey="dip_c1", candidate_profile=cand1, type_licence=type_licence_info, universite="ISSAT", annee_obtention="2024")
    LicenceYear.objects.create(pubkey="ly_c1_1", candidate_profile=cand1, type_licence=type_licence_info, annee=1, annee_universitaire="2021/2022", moyenne=12.0)
    LicenceYear.objects.create(pubkey="ly_c1_2", candidate_profile=cand1, type_licence=type_licence_info, annee=2, annee_universitaire="2022/2023", moyenne=12.0)
    LicenceYear.objects.create(pubkey="ly_c1_3", candidate_profile=cand1, type_licence=type_licence_info, annee=3, annee_universitaire="2023/2024", moyenne=12.0)

    app1 = ApplicationService.submit(cand1, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))
    assert app1.score == 12.0
    assert app1.rang == 1

    # Candidat 2 avec moyenne 15.0 -> Score = 15.0 > 12.0 -> Doit prendre Rang 1, et App 1 devient Rang 2
    cand2 = CandidateProfile.objects.create(
        pubkey="cand_2_rank",
        nom="Mejri",
        prenom="Sarra",
        cin="52345678",
        email="sarra@test.tn",
        telephone="52345678",
        ville="Tunis",
        nationalite="Tunisienne",
        annee_naissance=2000,
        statut="VALIDE",
    )
    Diplome.objects.create(pubkey="dip_c2", candidate_profile=cand2, type_licence=type_licence_info, universite="FST", annee_obtention="2024")
    LicenceYear.objects.create(pubkey="ly_c2_1", candidate_profile=cand2, type_licence=type_licence_info, annee=1, annee_universitaire="2021/2022", moyenne=15.0)
    LicenceYear.objects.create(pubkey="ly_c2_2", candidate_profile=cand2, type_licence=type_licence_info, annee=2, annee_universitaire="2022/2023", moyenne=15.0)
    LicenceYear.objects.create(pubkey="ly_c2_3", candidate_profile=cand2, type_licence=type_licence_info, annee=3, annee_universitaire="2023/2024", moyenne=15.0)

    app2 = ApplicationService.submit(cand2, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))
    assert app2.score == 15.0
    assert app2.rang == 1

    app1.refresh_from_db()
    assert app1.rang == 2

    # Double candidature par cand2 -> Erreur AlreadyApplied
    with pytest.raises(AlreadyApplied):
        ApplicationService.submit(cand2, SubmitApplicationDTO(master_pubkey=master_with_criteria.pubkey))
