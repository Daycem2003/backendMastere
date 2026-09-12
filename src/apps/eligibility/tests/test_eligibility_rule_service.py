from types import SimpleNamespace
from unittest.mock import patch

from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.domain.value_types import Operator, ValueType
from src.apps.eligibility.dto.eligibility_rule import CreateEligibilityRuleDTO
from src.apps.eligibility.services.eligibility_rule_service import EligibilityRuleService


@patch("src.apps.eligibility.services.eligibility_rule_service.EligibilityCriteria")
def test_create_serializes_rule_value_to_json(mock_model_cls):
    created = SimpleNamespace(pk=1)
    mock_model_cls.objects.create.return_value = created
    master = SimpleNamespace(pk=1, pubkey="mst_1")

    dto = CreateEligibilityRuleDTO(
        master_pubkey="mst_1",
        criterion="average",
        rule_value=RuleValueData(value_type=ValueType.NUMERIC, operator=Operator.GTE, value=12),
    )

    EligibilityRuleService.create(dto, master)

    call_kwargs = mock_model_cls.objects.create.call_args.kwargs
    assert '"value_type":"NUMERIC"' in call_kwargs["valeur"]
    assert call_kwargs["criterion"] == "average"


def test_update_only_touches_provided_fields():
    from src.apps.eligibility.dto.eligibility_rule import UpdateEligibilityRuleDTO

    saved_fields = []
    criteria = SimpleNamespace(obligatoire=True, valeur="old", save=lambda update_fields: saved_fields.extend(update_fields))

    EligibilityRuleService.update(criteria, UpdateEligibilityRuleDTO(obligatoire=False))

    assert criteria.obligatoire is False
    assert saved_fields == ["obligatoire"]
