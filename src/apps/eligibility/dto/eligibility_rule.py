from pydantic import BaseModel

from src.apps.eligibility.domain.rule_value import RuleValueData


class CreateEligibilityRuleDTO(BaseModel):
    master_pubkey: str
    criterion: str
    obligatoire: bool = True
    rule_value: RuleValueData


class UpdateEligibilityRuleDTO(BaseModel):
    obligatoire: bool | None = None
    rule_value: RuleValueData | None = None
