from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.masters.dto.master import (
    AddRequiredDocumentDTO,
    CreateMasterDTO,
    SetAcceptedLicenceTypesDTO,
    SetPasserellesDTO,
    SetScoreFormulaDTO,
    UpdateMasterDTO,
)
from src.apps.masters.exceptions.master_exceptions import MasterAccessForbidden, MasterNotFound
from src.apps.masters.permissions.master_permissions import CanCreateMaster
from src.apps.masters.policies.master_policy import MasterPolicy
from src.apps.masters.selectors.master_selector import get_by_pubkey, list_open
from src.apps.masters.serializers.master import (
    AddRequiredDocumentSerializer,
    CreateMasterSerializer,
    MasterSerializer,
    MasterSummarySerializer,
    ScoreFormulaSerializer,
    SetAcceptedLicenceTypesSerializer,
    SetPasserellesSerializer,
    SetScoreFormulaSerializer,
    UpdateMasterSerializer,
)
from src.apps.masters.services.master_service import MasterService
from src.apps.masters.services.score_service import RequiredDocumentService, ScoreService


class MasterListView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanCreateMaster()]
        return [permissions.AllowAny()]

    def get(self, request):
        domaine = request.query_params.get("domaine")
        return Response(
            MasterSummarySerializer(
                list_open(domaine=domaine),
                many=True
            ).data
        )

    def post(self, request):
        print("========== POST MASTER ==========")
        print("USER:", request.user)
        print("AUTH:", getattr(request.user, "is_authenticated", None))
        print("PUBKEY:", getattr(request.user, "pubkey", None))
        print("==================================")

        coordinateur = getattr(request.user, "coordinateur", None)

        if not coordinateur:
            raise MasterAccessForbidden()

        serializer = CreateMasterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = CreateMasterDTO(**serializer.validated_data)
        master = MasterService.create(dto, coordinateur)

        return Response(
            MasterSerializer(master).data,
            status=status.HTTP_201_CREATED
        )


class MasterDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        user = request.user if (request.user and getattr(request.user, "is_authenticated", False)) else None
        if not MasterPolicy.can_view(user, master):
            raise MasterAccessForbidden()
        return Response(MasterSerializer(master).data)

    def patch(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_edit(request.user, master):
            raise MasterAccessForbidden()

        serializer = UpdateMasterSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = UpdateMasterDTO(**serializer.validated_data)
        master = MasterService.update(master, dto)
        return Response(MasterSerializer(master).data)


class MasterAcceptedLicenceTypesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_edit(request.user, master):
            raise MasterAccessForbidden()

        serializer = SetAcceptedLicenceTypesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetAcceptedLicenceTypesDTO(**serializer.validated_data)
        master = MasterService.set_accepted_licence_types(master, dto)
        return Response(MasterSerializer(master).data)


class MasterPasserellesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_edit(request.user, master):
            raise MasterAccessForbidden()

        serializer = SetPasserellesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetPasserellesDTO(**serializer.validated_data)
        master = MasterService.set_passerelles(master, dto)
        return Response(MasterSerializer(master).data)


class MasterRequiredDocumentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_edit(request.user, master):
            raise MasterAccessForbidden()

        serializer = AddRequiredDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = AddRequiredDocumentDTO(**serializer.validated_data)
        doc = RequiredDocumentService.add(master, dto)
        return Response({"pubkey": doc.pubkey, "type": doc.type}, status=status.HTTP_201_CREATED)


class MasterScoreFormulaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_edit(request.user, master):
            raise MasterAccessForbidden()

        serializer = SetScoreFormulaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetScoreFormulaDTO(**serializer.validated_data)
        formula = ScoreService.set_formula(master, dto)
        return Response(ScoreFormulaSerializer(formula).data, status=status.HTTP_201_CREATED)


class PublishMasterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()
        if not MasterPolicy.can_publish(request.user, master):
            raise MasterAccessForbidden()
        master = MasterService.publish(master)
        return Response(MasterSerializer(master).data)
