import pytest
from django.utils import timezone

from src.apps.applications.dto.application import SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import NotEligible
from src.apps.applications.services.application_service import ApplicationService
from src.apps.candidate_profile.models import CandidateProfile, Diplome, LicenceYear, TypeLicence
from src.apps.coordinator.models import Coordinateur
from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.models import EligibilityCriteria
from src.apps.masters.models import Master, MasterStatus
from src.apps.users.models import User


@pytest.fixture
def type_licence_chimie(db):
    return TypeLicence.objects.create(pubkey="lic_chimie_01", intitule="Chimie")


@pytest.fixture
def type_licence_physique(db):
    return TypeLicence.objects.create(pubkey="lic_physique_01", intitule="Physique")


@pytest.fixture
def master_chimie_industrielle(db, type_licence_chimie):
    user = User.objects.create(pubkey="usr_coord_chimie", email="coord.chimie@test.tn", password="password")
    coord = Coordinateur.objects.create(pubkey="coord_chimie_pk", user=user, nom="Coord Chimie", email="coord.chimie@test.tn")
    now = timezone.now()

    master = Master.objects.create(
        pubkey="mst_chimie_ind_01",
        nom="Chimie Industrielle",
        universite="Université de Monastir",
        ville="Monastir",
        domaine="Sciences Fondamentales",
        discipline="Chimie",
        specialite="Chimie Industrielle",
        nombre_places=15,
        date_debut=now - timezone.timedelta(days=10),
        date_fin=now + timezone.timedelta(days=30),
        statut=MasterStatus.OUVERT,
        coordinateur=coord,
    )
    master.type_licences_acceptees.add(type_licence_chimie)

    # Critère 1: moyenne >= 11.0
    EligibilityCriteria.objects.create(
        pubkey="ec_chimie_avg",
        master=master,
        criterion="average",
        obligatoire=True,
        rule_value=RuleValueData(
            value_type=ValueType.NUMERIC,
            operator=Operator.GTE,
            value=11.0,
        ),
    )
    # Critère 2: nationalité == "Tunisienne"
    EligibilityCriteria.objects.create(
        pubkey="ec_chimie_nat",
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
def test_eligible_candidate_for_chimie_industrielle_submits_successfully(master_chimie_industrielle, type_licence_chimie):
    """Vérifie que le candidat remplissant les critères de Chimie Industrielle (moyenne >= 11.0, nationalité Tunisienne)
    n'est pas rejeté à tort."""
    candidate = CandidateProfile.objects.create(
        pubkey="cand_chimie_ok",
        nom="Fekih",
        prenom="Daycem",
        cin="09876543",
        email="daycem@test.tn",
        telephone="98765432",
        ville="Monastir",
        nationalite="Tunisienne",
        annee_naissance=2000,
        statut="VALIDE",
    )
    Diplome.objects.create(
        pubkey="dip_chimie_ok",
        candidate_profile=candidate,
        type_licence=type_licence_chimie,
        universite="Faculté des Sciences de Monastir",
        annee_obtention="2024",
    )
    # 3 années de Licence avec moyenne générale = 11.5 >= 11.0
    LicenceYear.objects.create(pubkey="ly_c_1", candidate_profile=candidate, type_licence=type_licence_chimie, annee=1, annee_universitaire="2021/2022", moyenne=11.0)
    LicenceYear.objects.create(pubkey="ly_c_2", candidate_profile=candidate, type_licence=type_licence_chimie, annee=2, annee_universitaire="2022/2023", moyenne=11.5)
    LicenceYear.objects.create(pubkey="ly_c_3", candidate_profile=candidate, type_licence=type_licence_chimie, annee=3, annee_universitaire="2023/2024", moyenne=12.0)

    app = ApplicationService.submit(candidate, SubmitApplicationDTO(master_pubkey=master_chimie_industrielle.pubkey))
    assert app is not None
    assert app.master == master_chimie_industrielle
    assert app.candidate_profile == candidate
    assert app.score == 11.5


@pytest.mark.django_db
def test_nationality_normalization_and_case_insensitivity(master_chimie_industrielle, type_licence_chimie):
    """Vérifie la robustesse de comparaison de nationalité (casse, espaces, variantes)."""
    candidate = CandidateProfile.objects.create(
        pubkey="cand_nat_variant",
        nom="Ben Amor",
        prenom="Mohamed",
        cin="01122334",
        email="mohamed@test.tn",
        telephone="99887766",
        ville="Sousse",
        nationalite=" tunisienne ",  # lowercase and spaces
        annee_naissance=1999,
        statut="VALIDE",
    )
    Diplome.objects.create(
        pubkey="dip_nat_variant",
        candidate_profile=candidate,
        type_licence=type_licence_chimie,
        universite="FSM",
        annee_obtention="2024",
    )
    LicenceYear.objects.create(pubkey="ly_nv_1", candidate_profile=candidate, type_licence=type_licence_chimie, annee=1, annee_universitaire="2021/2022", moyenne=12.0)
    LicenceYear.objects.create(pubkey="ly_nv_2", candidate_profile=candidate, type_licence=type_licence_chimie, annee=2, annee_universitaire="2022/2023", moyenne=12.0)
    LicenceYear.objects.create(pubkey="ly_nv_3", candidate_profile=candidate, type_licence=type_licence_chimie, annee=3, annee_universitaire="2023/2024", moyenne=12.0)

    app = ApplicationService.submit(candidate, SubmitApplicationDTO(master_pubkey=master_chimie_industrielle.pubkey))
    assert app is not None
    assert app.score == 12.0


@pytest.mark.django_db
def test_multi_diploma_matching_qualifies_candidate(master_chimie_industrielle, type_licence_chimie, type_licence_physique):
    """Vérifie qu'un candidat avec plusieurs diplômes dont l'un correspond aux critères du Master est accepté."""
    candidate = CandidateProfile.objects.create(
        pubkey="cand_multi_dip",
        nom="Jaziri",
        prenom="Ines",
        cin="03344556",
        email="ines@test.tn",
        telephone="97766554",
        ville="Tunis",
        nationalite="Tunisienne",
        annee_naissance=2001,
        statut="VALIDE",
    )
    # Diplome 1: Physique (non accepté directement pour Chimie)
    Diplome.objects.create(
        pubkey="dip_phys",
        candidate_profile=candidate,
        type_licence=type_licence_physique,
        universite="FST",
        annee_obtention="2023",
    )
    # Diplome 2: Chimie (accepté pour Chimie Industrielle)
    Diplome.objects.create(
        pubkey="dip_chim",
        candidate_profile=candidate,
        type_licence=type_licence_chimie,
        universite="FSM",
        annee_obtention="2024",
    )
    LicenceYear.objects.create(pubkey="ly_md_1", candidate_profile=candidate, type_licence=type_licence_chimie, annee=1, annee_universitaire="2021/2022", moyenne=13.0)
    LicenceYear.objects.create(pubkey="ly_md_2", candidate_profile=candidate, type_licence=type_licence_chimie, annee=2, annee_universitaire="2022/2023", moyenne=13.0)
    LicenceYear.objects.create(pubkey="ly_md_3", candidate_profile=candidate, type_licence=type_licence_chimie, annee=3, annee_universitaire="2023/2024", moyenne=13.0)

    app = ApplicationService.submit(candidate, SubmitApplicationDTO(master_pubkey=master_chimie_industrielle.pubkey))
    assert app is not None
    assert app.score == 13.0


@pytest.mark.django_db
def test_ineligible_candidate_returns_detailed_rejection(master_chimie_industrielle, type_licence_chimie):
    """Vérifie qu'un rejet légitime retourne des détails explicites sur les critères non satisfaits."""
    candidate = CandidateProfile.objects.create(
        pubkey="cand_ineligible_detail",
        nom="Smith",
        prenom="John",
        cin="99999999",
        email="john@test.com",
        telephone="11223344",
        ville="London",
        nationalite="Britannique",
        annee_naissance=2000,
        statut="VALIDE",
    )
    Diplome.objects.create(
        pubkey="dip_ineligible_detail",
        candidate_profile=candidate,
        type_licence=type_licence_chimie,
        universite="Oxford",
        annee_obtention="2024",
    )
    # Moyenne = 10.0 < 11.0
    LicenceYear.objects.create(pubkey="ly_in_1", candidate_profile=candidate, type_licence=type_licence_chimie, annee=1, annee_universitaire="2021/2022", moyenne=10.0)
    LicenceYear.objects.create(pubkey="ly_in_2", candidate_profile=candidate, type_licence=type_licence_chimie, annee=2, annee_universitaire="2022/2023", moyenne=10.0)
    LicenceYear.objects.create(pubkey="ly_in_3", candidate_profile=candidate, type_licence=type_licence_chimie, annee=3, annee_universitaire="2023/2024", moyenne=10.0)

    with pytest.raises(NotEligible) as exc_info:
        ApplicationService.submit(candidate, SubmitApplicationDTO(master_pubkey=master_chimie_industrielle.pubkey))

    assert "Moyenne minimale de Licence requise" in str(exc_info.value.detail)
    assert "Nationalité requise" in str(exc_info.value.detail)
