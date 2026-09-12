from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateDiplomeDTO,
    CreateLicenceYearDTO,
    CreateMaster1YearDTO,
    SetRedoublementDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    CandidateProfileNotFound,
)
from src.apps.candidate_profile.models import TypeLicence
from src.apps.candidate_profile.selectors.candidate_profile_selector import (
    get_by_onboarding_token,
    get_by_user,
)
from src.apps.candidate_profile.serializers.candidate_profile import (
    CreateDiplomeSerializer,
    CreateLicenceYearSerializer,
    CreateMaster1YearSerializer,
    DiplomeSerializer,
    LicenceYearSerializer,
    Master1YearSerializer,
    RedoublementSerializer,
    SetRedoublementSerializer,
    TypeLicenceSerializer,
)
from src.apps.candidate_profile.services.academic_record_service import AcademicRecordService


def _require_candidate_profile(request):
    """Résout le CandidateProfile de la requête selon deux voies :
    1. Utilisateur authentifié (compte créé après validation coordinateur)
       -> get_by_user.
    2. Jeton d'onboarding envoyé en en-tête X-Onboarding-Token (parcours de
       création, avant tout compte) -> get_by_onboarding_token.
    Aucune des deux ne doit jamais lever d'exception sur un `None` — on
    retombe systématiquement sur une 404 propre (CandidateProfileNotFound),
    jamais sur une AttributeError.
    """
    if request.user and request.user.is_authenticated:
        profile = get_by_user(request.user)
        if profile is not None:
            return profile

    token = request.headers.get("X-Onboarding-Token")
    profile = get_by_onboarding_token(token)
    if profile is not None:
        return profile

    raise CandidateProfileNotFound()


class TypeLicenceListView(View):
    def get(self, request):
        data = (
            TypeLicence.objects.filter(
                deleted_at__isnull=True,
                est_eligible=True,
            )
            .order_by("intitule")
            .values("pubkey", "intitule", "domaine")
        )

        results = [
            {"pubkey": d["pubkey"], "intitule": d["intitule"], "domaine": d["domaine"]}
            for d in data
        ]
        return JsonResponse({"results": results})


class LicenceYearListView(APIView):
    # AllowAny : la résolution du profil se fait via _require_candidate_profile
    # (utilisateur authentifié OU jeton d'onboarding). Le rejet se fait au
    # niveau applicatif (CandidateProfileNotFound), pas au niveau permission.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        profile = _require_candidate_profile(request)
        years = profile.licence_years.filter(deleted_at__isnull=True)
        return Response(LicenceYearSerializer(years, many=True).data)

    def post(self, request):
        profile = _require_candidate_profile(request)
        serializer = CreateLicenceYearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateLicenceYearDTO(**serializer.validated_data)
        licence_year = AcademicRecordService.add_licence_year(profile, dto)
        return Response(LicenceYearSerializer(licence_year).data, status=status.HTTP_201_CREATED)


class DiplomeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        profile = _require_candidate_profile(request)
        serializer = CreateDiplomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateDiplomeDTO(**serializer.validated_data)
        diplome = AcademicRecordService.set_diplome(profile, dto)
        return Response(DiplomeSerializer(diplome).data, status=status.HTTP_201_CREATED)


class Master1YearView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        profile = _require_candidate_profile(request)
        serializer = CreateMaster1YearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateMaster1YearDTO(**serializer.validated_data)
        m1 = AcademicRecordService.set_master1_year(profile, dto)
        return Response(Master1YearSerializer(m1).data)


class RedoublementView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        profile = _require_candidate_profile(request)
        serializer = SetRedoublementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetRedoublementDTO(**serializer.validated_data)
        redoublement = AcademicRecordService.set_redoublement(profile, dto)
        return Response(RedoublementSerializer(redoublement).data)