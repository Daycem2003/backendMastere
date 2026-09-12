from rest_framework import permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
from src.apps.candidate_profile.selectors.candidate_profile_selector import (
    get_by_pubkey,
    get_by_user,
    list_candidate_profiles,
)
from src.apps.candidate_profile.serializers.candidate_profile import (
    CandidateProfileSerializer,
    CreateCandidateProfileSerializer,
    UpdateCandidateProfileSerializer,
)
from src.apps.candidate_profile.services.candidate_profile_service import CandidateProfileService
from src.apps.reference_data.constants import NATIONALITIES


from .academic_record_views import _require_candidate_profile


class MyCandidateProfileView(APIView):
    def get_permissions(self):
        # Permettre l'accès public pour la création, ou pour consultation/mise à
        # jour avec le jeton d'onboarding (ex. lors d'une demande de révision).
        if self.request.method == "POST" or self.request.headers.get("X-Onboarding-Token"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        profile = _require_candidate_profile(request)
        data = CandidateProfileSerializer(profile).data
        if not profile.user_id:
            data["onboarding_token"] = profile.onboarding_token
        return Response(data)

    def post(self, request):
        serializer = CreateCandidateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateCandidateProfileDTO(**serializer.validated_data)

        user = request.user if request.user and request.user.is_authenticated else None

        profile = CandidateProfileService.create_profile(dto, user)

        # Le jeton n'est exposé que dans cette réponse de création : c'est
        # le seul moment où le frontend en a besoin (pour l'utiliser ensuite
        # comme en-tête X-Onboarding-Token sur les appels licence-years,
        # diplome, master1-year, redoublement). Ajouté manuellement plutôt que
        # via le serializer pour garantir qu'il ne fuite jamais sur GET/detail,
        # même si CandidateProfileSerializer venait un jour à inclure ce champ.
        data = CandidateProfileSerializer(profile).data
        data["onboarding_token"] = profile.onboarding_token

        return Response(data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = _require_candidate_profile(request)
        serializer = UpdateCandidateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = UpdateCandidateProfileDTO(**serializer.validated_data)
        user = request.user if request.user and request.user.is_authenticated else None
        profile = CandidateProfileService.update_profile(profile, dto, user)
        return Response(CandidateProfileSerializer(profile).data)



class NationalityListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(NATIONALITIES)


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


class CandidateProfileListView(APIView):
    """Consultation de la liste des candidatures par un coordinateur ou administrateur."""

    permission_classes = [CanViewAnyProfile]

    def get(self, request):
        statut = request.query_params.get("statut")
        q = request.query_params.get("q")
        profiles = list_candidate_profiles(statut=statut, q=q)
        return Response(CandidateProfileSerializer(profiles, many=True).data)