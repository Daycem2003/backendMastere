from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.applications.dto.application import DecisionDTO, SubmitApplicationDTO
from src.apps.applications.exceptions.application_exceptions import (
    ApplicationAccessForbidden,
    ApplicationNotFound,
    ApplicationNotWithdrawable,
    CandidateProfileRequired,
)
from src.apps.applications.permissions.application_permissions import CanReviewApplications
from src.apps.applications.policies.application_policy import ApplicationPolicy
from src.apps.applications.selectors.application_selector import get_by_pubkey, list_for_candidate
from src.apps.applications.serializers.application import (
    ApplicationSerializer,
    DecisionSerializer,
    SubmitApplicationSerializer,
)
from src.apps.applications.services.application_service import ApplicationService
from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_user


def _require_profile(request):
    profile = get_by_user(request.user)
    if not profile:
        raise CandidateProfileRequired()
    return profile


class SubmitApplicationView(APIView):
    """Le candidat clique simplement "postuler" avec le master visé — la
    résolution du niveau (M1 classique vs M2 passerelle) et la vérification
    des documents/éligibilité sont entièrement gérées par le service."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = _require_profile(request)
        serializer = SubmitApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SubmitApplicationDTO(**serializer.validated_data)
        application = ApplicationService.submit(profile, dto)
        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class MyApplicationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _require_profile(request)
        applications = list_for_candidate(profile.pubkey)
        return Response(ApplicationSerializer(applications, many=True).data)


class ApplicationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        application = get_by_pubkey(pubkey)
        if not application:
            raise ApplicationNotFound()
        if not ApplicationPolicy.can_view(request.user, application):
            raise ApplicationAccessForbidden()
        return Response(ApplicationSerializer(application).data)


class WithdrawApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pubkey):
        application = get_by_pubkey(pubkey)
        if not application:
            raise ApplicationNotFound()
        if not ApplicationPolicy.can_withdraw(request.user, application):
            raise ApplicationNotWithdrawable()
        ApplicationService.withdraw(application)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DecideApplicationView(APIView):
    permission_classes = [CanReviewApplications]

    def post(self, request, pubkey):
        application = get_by_pubkey(pubkey)
        if not application:
            raise ApplicationNotFound()
        self.check_object_permissions(request, application)
        if not ApplicationPolicy.can_decide(request.user, application):
            raise ApplicationAccessForbidden()

        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = DecisionDTO(**serializer.validated_data)
        application = ApplicationService.decide(application, dto, request.user)
        return Response(ApplicationSerializer(application).data)
