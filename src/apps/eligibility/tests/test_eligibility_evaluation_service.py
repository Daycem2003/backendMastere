from datetime import date
from types import SimpleNamespace

from src.apps.eligibility.domain.candidate_snapshot import CandidateSnapshot
from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.services.eligibility_evaluation_service import EligibilityService


def _criteria(criterion, rule_value, obligatoire=True):
    return SimpleNamespace(criterion=criterion, rule_value=rule_value, obligatoire=obligatoire)


# --- Numérique (moyenne) ------------------------------------------------

def test_average_above_threshold_passes():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    snapshot = CandidateSnapshot(average=15)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("average", rule)) is None


def test_average_below_threshold_fails():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    snapshot = CandidateSnapshot(average=10.8)
    failure = EligibilityService.evaluate_rule(snapshot, _criteria("average", rule))
    assert failure is not None
    assert failure.criterion == "average"
    assert failure.actual == "10.8"


def test_average_equals_threshold_passes_with_gte():
    """Cas limite section 11 : average == threshold."""
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    snapshot = CandidateSnapshot(average=12)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("average", rule)) is None


# --- Redoublements --------------------------------------------------------

def test_repeated_years_within_limit_passes():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.LTE, value=1)
    snapshot = CandidateSnapshot(repeated_years=1)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("repeated_years", rule)) is None


def test_repeated_years_exceeded_fails():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.LTE, value=1)
    snapshot = CandidateSnapshot(repeated_years=2)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("repeated_years", rule)) is not None


def test_repeated_years_equals_maximum_allowed_passes():
    """Cas limite section 11 : repeated_years == maximum_allowed."""
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.LTE, value=1)
    snapshot = CandidateSnapshot(repeated_years=1)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("repeated_years", rule)) is None


# --- Dates ------------------------------------------------------------

def test_graduation_date_within_range_passes():
    rule = RuleValueData(value_type=ValueType.DATE_RANGE, min_value="2024-01-01", max_value="2026-06-30")
    snapshot = CandidateSnapshot(graduation_date=date(2025, 6, 15))
    assert EligibilityService.evaluate_rule(snapshot, _criteria("graduation_date", rule)) is None


def test_graduation_date_outside_range_fails():
    rule = RuleValueData(value_type=ValueType.DATE_RANGE, min_value="2024-01-01", max_value="2026-06-30")
    snapshot = CandidateSnapshot(graduation_date=date(2027, 1, 1))
    assert EligibilityService.evaluate_rule(snapshot, _criteria("graduation_date", rule)) is not None


# --- Université ---------------------------------------------------------

def test_university_in_allowed_list_passes():
    rule = RuleValueData(
        value_type=ValueType.STRING, operator=Operator.IN,
        values=["Université de Sousse", "Université de Tunis"],
    )
    snapshot = CandidateSnapshot(university_name="Université de Tunis")
    assert EligibilityService.evaluate_rule(snapshot, _criteria("university_name", rule)) is None


def test_university_not_in_allowed_list_fails():
    rule = RuleValueData(
        value_type=ValueType.STRING, operator=Operator.IN,
        values=["Université de Sousse"],
    )
    snapshot = CandidateSnapshot(university_name="Université de Sfax")
    assert EligibilityService.evaluate_rule(snapshot, _criteria("university_name", rule)) is not None


# --- Nationalité ---------------------------------------------------------

def test_accepted_nationality_passes():
    rule = RuleValueData(value_type=ValueType.ENUM, operator=Operator.EQ, value="Tunisian")
    snapshot = CandidateSnapshot(nationality="Tunisian")
    assert EligibilityService.evaluate_rule(snapshot, _criteria("nationality", rule)) is None


def test_rejected_nationality_fails():
    rule = RuleValueData(value_type=ValueType.ENUM, operator=Operator.EQ, value="Tunisian")
    snapshot = CandidateSnapshot(nationality="French")
    assert EligibilityService.evaluate_rule(snapshot, _criteria("nationality", rule)) is not None


# --- Combinaison / master sans règle / donnée manquante -----------------

def test_missing_required_data_fails_with_explicit_reason():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    snapshot = CandidateSnapshot(average=None)
    failure = EligibilityService.evaluate_rule(snapshot, _criteria("average", rule, obligatoire=True))
    assert failure is not None
    assert "manquante" in failure.reason


def test_missing_optional_data_does_not_fail():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    snapshot = CandidateSnapshot(average=None)
    assert EligibilityService.evaluate_rule(snapshot, _criteria("average", rule, obligatoire=False)) is None


def test_evaluate_combines_multiple_criteria_as_and():
    """Combinaison de plusieurs critères — un seul échec suffit à rendre
    le candidat inéligible (AND cumulatif, section 5)."""
    master = SimpleNamespace(
        pubkey="mst_1",
        type_licences_acceptees=SimpleNamespace(
            all=lambda: [SimpleNamespace(intitule="Informatique")],
            values_list=lambda field, flat: ["lic_info"],
        ),
    )
    snapshot = CandidateSnapshot(licence_type_code="lic_info", average=10, repeated_years=0)

    from unittest.mock import patch

    with patch(
        "src.apps.eligibility.services.eligibility_evaluation_service.list_for_master",
        return_value=[
            _criteria("average", RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)),
            _criteria("repeated_years", RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.LTE, value=1)),
        ],
    ):
        result = EligibilityService.evaluate(snapshot, master)

    assert result.eligible is False
    assert len(result.failed_rules) == 1  # seule "average" échoue
    assert result.failed_rules[0].criterion == "average"


def test_master_without_any_rule_is_eligible_by_licence_type_alone():
    master = SimpleNamespace(
        pubkey="mst_1",
        type_licences_acceptees=SimpleNamespace(
            all=lambda: [SimpleNamespace(intitule="Informatique")],
            values_list=lambda field, flat: ["lic_info"],
        ),
    )
    snapshot = CandidateSnapshot(licence_type_code="lic_info")

    from unittest.mock import patch

    with patch(
        "src.apps.eligibility.services.eligibility_evaluation_service.list_for_master", return_value=[]
    ):
        result = EligibilityService.evaluate(snapshot, master)

    assert result.eligible is True
    assert result.failed_rules == []


def test_candidate_without_accepted_licence_type_is_never_eligible():
    """Section 6 : posséder une licence ne suffit pas — le type doit être
    accepté par le master."""
    master = SimpleNamespace(
        pubkey="mst_1",
        type_licences_acceptees=SimpleNamespace(
            all=lambda: [SimpleNamespace(intitule="Informatique")],
            values_list=lambda field, flat: ["lic_info"],
        ),
    )
    snapshot = CandidateSnapshot(licence_type_code="lic_math", average=18)

    from unittest.mock import patch

    with patch(
        "src.apps.eligibility.services.eligibility_evaluation_service.list_for_master", return_value=[]
    ):
        result = EligibilityService.evaluate(snapshot, master)

    assert result.eligible is False
    assert result.failed_rules[0].criterion == "licence_type"
