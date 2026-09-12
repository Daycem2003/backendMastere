import pytest
from pydantic import ValidationError

from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType


def test_numeric_rule_valid():
    rule = RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12)
    assert rule.value == 12


def test_numeric_range_min_max_valid():
    rule = RuleValueData(value_type=ValueType.NUMERIC_RANGE, min_value=10, max_value=14)
    assert rule.min_value == 10


def test_numeric_range_rejects_min_greater_than_max():
    """Cas limite section 8 : NUMERIC_RANGE doit vérifier min <= max."""
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.NUMERIC_RANGE, min_value=15, max_value=10)


def test_numeric_range_min_equals_max_is_valid():
    """Cas limite explicite de la spec : min == max."""
    rule = RuleValueData(value_type=ValueType.NUMERIC_RANGE, min_value=12, max_value=12)
    assert rule.min_value == rule.max_value == 12


def test_date_range_requires_valid_dates():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.DATE_RANGE, min_value="pas-une-date", max_value="2026-06-30")


def test_date_range_date_from_equals_date_to_is_valid():
    """Cas limite : date_from == date_to."""
    rule = RuleValueData(value_type=ValueType.DATE_RANGE, min_value="2026-01-01", max_value="2026-01-01")
    assert rule.min_value == rule.max_value


def test_date_range_rejects_from_after_to():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.DATE_RANGE, min_value="2026-06-30", max_value="2026-01-01")


def test_range_requires_at_least_one_bound():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.NUMERIC_RANGE)


def test_numeric_criterion_rejects_non_numeric_value():
    """Section 8 : un critère DATE/NUMERIC ne doit pas recevoir une valeur
    incompatible."""
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value="douze")


def test_numeric_operator_cannot_be_used_with_string_type():
    """Section 8 : un opérateur numérique ne doit pas être utilisé avec un
    type STRING."""
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.STRING, operator=Operator.GTE, value="Tunisian")


def test_string_in_operator_requires_values_list():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.STRING, operator=Operator.IN)


def test_string_in_operator_valid_with_values():
    rule = RuleValueData(
        value_type=ValueType.STRING,
        operator=Operator.IN,
        values=["Université de Sousse", "Université de Tunis"],
    )
    assert len(rule.values) == 2


def test_nationality_as_enum_equality():
    rule = RuleValueData(value_type=ValueType.ENUM, operator=Operator.EQ, value="Tunisian")
    assert rule.value == "Tunisian"


def test_boolean_rejects_non_boolean_value():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.BOOLEAN, operator=Operator.EQ, value="yes")


def test_date_rejects_invalid_format():
    with pytest.raises(ValidationError):
        RuleValueData(value_type=ValueType.DATE, operator=Operator.GTE, value="30/06/2026")


def test_serialization_roundtrip():
    rule = RuleValueData(value_type=ValueType.NUMERIC_RANGE, min_value=10, max_value=14)
    restored = RuleValueData.from_json(rule.to_json())
    assert restored == rule
