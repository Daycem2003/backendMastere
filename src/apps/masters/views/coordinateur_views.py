from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.masters.dto.master import (
    CreateEligibilityCriteriaDTO,
    CreateRequiredDocumentDTO,
    SetPasserellesDTO,
    SetScoreFormulaDTO,
)
from src.apps.masters.exceptions.master_exceptions import MasterAccessForbidden, MasterNotFound
from src.apps.masters.permissions.master_permissions import CanCreateMaster
from src.apps.masters.policies.master_policy import MasterPolicy
from src.apps.masters.selectors.master_selector import get_by_pubkey
from src.apps.masters.serializers.master import (
    CreateEligibilityCriteriaSerializer,
    CreateRequiredDocumentSerializer,
    EligibilityCriteriaSerializer,
    RequiredDocumentSerializer,
    ScoreFormulaSerializer,
    SetPasserellesSerializer,
    SetScoreFormulaSerializer,
)
from src.apps.masters.services.eligibility_criteria_service import EligibilityCriteriaService


def _own_editable_master(request, pubkey):
    master = get_by_pubkey(pubkey)
    if not master:
        raise MasterNotFound()
    if not MasterPolicy.can_edit(request.user, master):
        raise MasterAccessForbidden()
    return master


class EligibilityCriteriaListView(APIView):
    permission_classes = [CanCreateMaster]

    def post(self, request, pubkey):
        master = _own_editable_master(request, pubkey)
        serializer = CreateEligibilityCriteriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateEligibilityCriteriaDTO(**serializer.validated_data)
        criteria = EligibilityCriteriaService.add_criteria(master, dto)
        return Response(EligibilityCriteriaSerializer(criteria).data, status=status.HTTP_201_CREATED)


class ScoreFormulaView(APIView):
    permission_classes = [CanCreateMaster]

    def put(self, request, pubkey):
        master = _own_editable_master(request, pubkey)
        serializer = SetScoreFormulaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetScoreFormulaDTO(**serializer.validated_data)
        formula = EligibilityCriteriaService.set_score_formula(master, dto)
        return Response(ScoreFormulaSerializer(formula).data, status=status.HTTP_200_OK)


class RequiredDocumentListView(APIView):
    permission_classes = [CanCreateMaster]

    def post(self, request, pubkey):
        master = _own_editable_master(request, pubkey)
        serializer = CreateRequiredDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateRequiredDocumentDTO(**serializer.validated_data)
        document = EligibilityCriteriaService.add_required_document(master, dto)
        return Response(RequiredDocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class PasserellesView(APIView):
    permission_classes = [CanCreateMaster]

    def put(self, request, pubkey):
        master = _own_editable_master(request, pubkey)
        serializer = SetPasserellesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetPasserellesDTO(**serializer.validated_data)
        EligibilityCriteriaService.set_passerelles(master, dto)
        return Response({"passerelles_vers": dto.master_pubkeys})
