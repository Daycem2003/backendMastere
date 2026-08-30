from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateDiplomeDTO,
    CreateLicenceYearDTO,
    CreateMaster1YearDTO,
    SetRedoublementDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    CandidateProfileNotFound,
    ProfileNotEditable,
)
from src.apps.candidate_profile.policies.candidate_profile_policy import CandidateProfilePolicy
from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_user
from src.apps.candidate_profile.serializers.candidate_profile import (
    CreateDiplomeSerializer,
    CreateLicenceYearSerializer,
    CreateMaster1YearSerializer,
    DiplomeSerializer,
    LicenceYearSerializer,
    Master1YearSerializer,
    RedoublementSerializer,
    SetRedoublementSerializer,
)
from src.apps.candidate_profile.services.academic_record_service import AcademicRecordService


def _own_editable_profile(request):
    profile = get_by_user(request.user)
    if not profile:
        raise CandidateProfileNotFound()
    if not CandidateProfilePolicy.can_edit(request.user, profile):
        raise ProfileNotEditable()
    return profile


class LicenceYearListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = _own_editable_profile(request)
        serializer = CreateLicenceYearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateLicenceYearDTO(**serializer.validated_data)
        year = AcademicRecordService.add_licence_year(profile, dto)
        return Response(LicenceYearSerializer(year).data, status=status.HTTP_201_CREATED)


class DiplomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        profile = _own_editable_profile(request)
        serializer = CreateDiplomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateDiplomeDTO(**serializer.validated_data)
        diplome = AcademicRecordService.set_diplome(profile, dto)
        return Response(DiplomeSerializer(diplome).data, status=status.HTTP_201_CREATED)


class Master1YearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        profile = _own_editable_profile(request)
        serializer = CreateMaster1YearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = CreateMaster1YearDTO(**serializer.validated_data)
        m1 = AcademicRecordService.set_master1_year(profile, dto)
        return Response(Master1YearSerializer(m1).data, status=status.HTTP_201_CREATED)


class RedoublementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        profile = _own_editable_profile(request)
        serializer = SetRedoublementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetRedoublementDTO(**serializer.validated_data)
        redoublement = AcademicRecordService.set_redoublement(profile, dto)
        return Response(RedoublementSerializer(redoublement).data, status=status.HTTP_201_CREATED)
