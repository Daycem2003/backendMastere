from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.eligibility.domain.rule_value import RuleValueData
from src.apps.eligibility.dto.eligibility_rule import (
    CreateEligibilityRuleDTO,
    UpdateEligibilityRuleDTO,
)
from src.apps.eligibility.exceptions.eligibility_exceptions import (
    EligibilityAccessForbidden,
    EligibilityRuleNotFound,
)
from src.apps.eligibility.permissions.eligibility_permissions import CanManageEligibilityRules
from src.apps.eligibility.policies.eligibility_policy import EligibilityRulePolicy
from src.apps.eligibility.selectors.eligibility_selector import get_by_pubkey, list_for_master
from src.apps.eligibility.serializers.eligibility_rule import (
    CreateEligibilityRuleSerializer,
    EligibilityCriteriaSerializer,
    EligibilityResultSerializer,
    UpdateEligibilityRuleSerializer,
)
from src.apps.eligibility.services.candidate_snapshot_resolver import (
    build_snapshot_from_candidate_profile,
)
from src.apps.eligibility.services.eligibility_evaluation_service import EligibilityService
from src.apps.eligibility.services.eligibility_rule_service import EligibilityRuleService
from src.apps.masters.exceptions.master_exceptions import MasterNotFound
from src.apps.masters.selectors.master_selector import get_by_pubkey as get_master_by_pubkey


class MasterEligibilityRuleListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, master_pubkey):
        rules = list_for_master(master_pubkey)
        return Response(EligibilityCriteriaSerializer(rules, many=True).data)

    def post(self, request, master_pubkey):
        master = get_master_by_pubkey(master_pubkey)
        if not master:
            raise MasterNotFound()
        if not EligibilityRulePolicy.can_manage(request.user, master):
            raise EligibilityAccessForbidden()

        serializer = CreateEligibilityRuleSerializer(data={**request.data, "master_pubkey": master_pubkey})
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        dto = CreateEligibilityRuleDTO(
            master_pubkey=master_pubkey,
            criterion=validated["criterion"],
            obligatoire=validated["obligatoire"],
            rule_value=RuleValueData(**validated["rule_value"]),
        )
        criteria = EligibilityRuleService.create(dto, master)
        return Response(EligibilityCriteriaSerializer(criteria).data, status=status.HTTP_201_CREATED)


class EligibilityRuleDetailView(APIView):
    permission_classes = [CanManageEligibilityRules]

    def patch(self, request, pubkey):
        criteria = get_by_pubkey(pubkey)
        if not criteria:
            raise EligibilityRuleNotFound()
        self.check_object_permissions(request, criteria)

        serializer = UpdateEligibilityRuleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        dto = UpdateEligibilityRuleDTO(
            obligatoire=validated.get("obligatoire"),
            rule_value=RuleValueData(**validated["rule_value"]) if "rule_value" in validated else None,
        )
        criteria = EligibilityRuleService.update(criteria, dto)
        return Response(EligibilityCriteriaSerializer(criteria).data)

    def delete(self, request, pubkey):
        criteria = get_by_pubkey(pubkey)
        if not criteria:
            raise EligibilityRuleNotFound()
        self.check_object_permissions(request, criteria)
        EligibilityRuleService.delete(criteria)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckCandidateEligibilityView(APIView):
    """Vérifie l'éligibilité du candidat authentifié pour un master donné."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, master_pubkey):
        from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
            CandidateProfileNotFound,
        )
        from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_user

        master = get_master_by_pubkey(master_pubkey)
        if not master:
            raise MasterNotFound()

        profile = get_by_user(request.user)
        if not profile:
            raise CandidateProfileNotFound()

        snapshot = build_snapshot_from_candidate_profile(profile, master)
        result = EligibilityService.evaluate(snapshot, master)
        return Response(EligibilityResultSerializer.from_result(result))
