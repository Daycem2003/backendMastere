from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateCandidateProfileDTO,
    UpdateCandidateProfileDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    CandidateProfileNotFound,
    ProfileAccessForbidden,
)
from src.apps.candidate_profile.permissions.candidate_profile_permissions import CanViewAnyProfile
from src.apps.candidate_profile.policies.candidate_profile_policy import CandidateProfilePolicy
from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_pubkey, get_by_user
from src.apps.candidate_profile.serializers.candidate_profile import (
    CandidateProfileSerializer,
    CreateCandidateProfileSerializer,
    UpdateCandidateProfileSerializer,
)
from src.apps.candidate_profile.services.candidate_profile_service import CandidateProfileService


class MyCandidateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_by_user(request.user)
        if not profile:
            raise CandidateProfileNotFound()
        return Response(CandidateProfileSerializer(profile).data)

    def post(self, request):
        serializer = CreateCandidateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateCandidateProfileDTO(**serializer.validated_data)
        profile = CandidateProfileService.create_profile(dto, request.user)
        return Response(CandidateProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = get_by_user(request.user)
        if not profile:
            raise CandidateProfileNotFound()
        serializer = UpdateCandidateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = UpdateCandidateProfileDTO(**serializer.validated_data)
        profile = CandidateProfileService.update_profile(profile, dto, request.user)
        return Response(CandidateProfileSerializer(profile).data)


class CandidateProfileDetailView(APIView):
    """Consultation par un coordinateur/admin (revue de candidature) ou par
    le propriétaire lui-même via son pubkey."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        profile = get_by_pubkey(pubkey)
        if not profile:
            raise CandidateProfileNotFound()
        if not CandidateProfilePolicy.can_view(request.user, profile):
            raise ProfileAccessForbidden()
        return Response(CandidateProfileSerializer(profile).data)
