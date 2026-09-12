from rest_framework import serializers

from src.apps.eligibility.domain.eligibility_result import EligibilityResult, FailedRule
from src.apps.eligibility.models import EligibilityCriteria


class RuleValueSerializer(serializers.Serializer):
    value_type = serializers.CharField()
    operator = serializers.CharField(required=False, allow_null=True)
    value = serializers.JSONField(required=False, allow_null=True)
    values = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    min_value = serializers.JSONField(required=False, allow_null=True)
    max_value = serializers.JSONField(required=False, allow_null=True)
    min_inclusive = serializers.BooleanField(required=False, default=True)
    max_inclusive = serializers.BooleanField(required=False, default=True)


class CreateEligibilityRuleSerializer(serializers.Serializer):
    master_pubkey = serializers.CharField()
    criterion = serializers.CharField(max_length=100)
    obligatoire = serializers.BooleanField(default=True)
    rule_value = RuleValueSerializer()


class UpdateEligibilityRuleSerializer(serializers.Serializer):
    obligatoire = serializers.BooleanField(required=False)
    rule_value = RuleValueSerializer(required=False)


class EligibilityCriteriaSerializer(serializers.ModelSerializer):
    rule_value = serializers.SerializerMethodField()

    class Meta:
        model = EligibilityCriteria
        fields = ("pubkey", "criterion", "obligatoire", "rule_value")
        read_only_fields = fields

    def get_rule_value(self, obj) -> dict:
        return obj.rule_value.model_dump(mode="json")


class FailedRuleSerializer(serializers.Serializer):
    criterion = serializers.CharField()
    expected = serializers.CharField()
    actual = serializers.CharField()
    reason = serializers.CharField()


class EligibilityResultSerializer(serializers.Serializer):
    eligible = serializers.BooleanField()
    failed_rules = FailedRuleSerializer(many=True)

    @staticmethod
    def from_result(result: EligibilityResult) -> dict:
        return {
            "eligible": result.eligible,
            "failed_rules": [f.model_dump() for f in result.failed_rules],
        }
