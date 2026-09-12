from pydantic import ValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.candidate_profile.permissions.candidate_profile_permissions import (
    CanViewAnyProfile,
)
from src.apps.candidate_profile.serializers.candidate_profile import (
    CandidateProfileSerializer,
)
from src.apps.coordinator.dto.decision import (
    RejectCandidatureDTO,
    RequestRevisionDTO,
)
from src.apps.coordinator.services.coordinator_decision_service import (
    CoordinatorDecisionService,
)


def _validate_dto(dto_class, data):
    try:
        return dto_class.model_validate(data or {})
    except ValidationError as error:
        raise DRFValidationError(error.errors()) from error


class ApproveCandidatureView(APIView):
    permission_classes = [CanViewAnyProfile]

    def post(self, request, pubkey):
        profile = CoordinatorDecisionService.approve_candidature(
            pubkey=pubkey,
            actor_user=request.user,
        )
        return Response(
            {
                "message": "Candidature approuvée avec succès. L'email d'activation a été envoyé.",
                "profile": CandidateProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )


class RejectCandidatureView(APIView):
    permission_classes = [CanViewAnyProfile]

    def post(self, request, pubkey):
        dto = _validate_dto(RejectCandidatureDTO, request.data)
        profile = CoordinatorDecisionService.reject_candidature(
            pubkey=pubkey,
            motif=dto.motif,
            actor_user=request.user,
        )
        return Response(
            {
                "message": "Candidature rejetée. L'email de notification a été envoyé.",
                "profile": CandidateProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )


class RequestRevisionView(APIView):
    permission_classes = [CanViewAnyProfile]

    def post(self, request, pubkey):
        dto = _validate_dto(RequestRevisionDTO, request.data)
        profile = CoordinatorDecisionService.request_revision(
            pubkey=pubkey,
            message=dto.message,
            documents_a_redeposer=dto.documents_a_redeposer,
            actor_user=request.user,
        )
        return Response(
            {
                "message": "Demande de révision envoyée avec succès au candidat.",
                "profile": CandidateProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )
