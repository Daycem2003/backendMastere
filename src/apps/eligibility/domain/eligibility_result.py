from pydantic import BaseModel


class FailedRule(BaseModel):
    criterion: str
    expected: str
    actual: str
    reason: str


class EligibilityResult(BaseModel):
    eligible: bool
    failed_rules: list[FailedRule] = []
