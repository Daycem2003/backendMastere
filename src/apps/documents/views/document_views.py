from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.candidate_profile.selectors.candidate_profile_selector import (
    get_by_onboarding_token,
    get_by_user,
)
from src.apps.documents.dto.document import DocumentSlotIdentityDTO, DocumentUploadDTO
from src.apps.documents.exceptions.document_exceptions import NoCandidateProfile
from src.apps.documents.permissions.document_permissions import (
    CanReviewDocuments,
    IsDocumentOwnerOrReviewer,
)
from src.apps.documents.selectors.document_selector import (
    list_candidate_slots,
    list_candidate_versions,
    list_pending_versions,
)
from src.apps.documents.serializers.document import (
    DocumentRejectionSerializer,
    DocumentSlotSerializer,
    DocumentUploadSerializer,
    DocumentVersionSerializer,
)
from src.apps.documents.services.document_service import DocumentService
from src.apps.documents.services.usage_budget import get_budgeted_storage


def _require_candidate_profile(request):
    """Résout le CandidateProfile de la requête selon deux voies :
    1. Utilisateur authentifié (compte candidat connecté) -> get_by_user.
    2. Jeton d'onboarding envoyé en en-tête X-Onboarding-Token (parcours de
       création, avant tout compte) -> get_by_onboarding_token.
    """
    if request.user and request.user.is_authenticated:
        profile = get_by_user(request.user)
        if profile is not None:
            return profile

    token = request.headers.get("X-Onboarding-Token")
    if token:
        profile = get_by_onboarding_token(token)
        if profile is not None:
            return profile

    raise NoCandidateProfile()


class MySlotListView(APIView):
    """Candidat : liste ses slots avec leur version courante — pratique
    pour un récapitulatif front (statut par pièce attendue)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        profile = _require_candidate_profile(request)
        slots = list_candidate_slots(profile.pubkey)
        return Response(
            DocumentSlotSerializer(slots, many=True, context={"storage": get_budgeted_storage()}).data
        )


class MyDocumentListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        profile = _require_candidate_profile(request)
        versions = list_candidate_versions(profile.pubkey)
        return Response(
            DocumentVersionSerializer(versions, many=True, context={"storage": get_budgeted_storage()}).data
        )


class DocumentUploadView(APIView):
    """Candidat : upload initial OU remplacement d'un de ses slots. Le slot
    est identifié par (slot_type, domaine, annee_licence,
    redoublement_annee, justificatif_index) — jamais par un pubkey de slot
    fourni par le client (get_or_create côté service, scope toujours ==
    profile courant)."""

    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = _require_candidate_profile(request)

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        uploaded_file = data["file"]

        storage = get_budgeted_storage()
        stored = DocumentService.store_uploaded_file(uploaded_file, profile, storage)

        payload = DocumentUploadDTO(
            candidate_profile_pubkey=profile.pubkey,
            slot=DocumentSlotIdentityDTO(
                slot_type=data["slot_type"],
                domaine=data["domaine"],
                annee_licence=data["annee_licence"],
                redoublement_annee=data["redoublement_annee"],
                justificatif_index=data["justificatif_index"],
            ),
            **stored,
        )
        version = DocumentService.create_version(payload, request.user)
        return Response(
            DocumentVersionSerializer(
                version, context={"storage": storage, "include_download_url": True}
            ).data,
            status=status.HTTP_201_CREATED,
        )


class PendingDocumentListView(APIView):
    """Coordinateur/Administrateur : file d'attente, accès global (aucun
    scope par Master — règle métier validée)."""

    permission_classes = [CanReviewDocuments]

    def get(self, request):
        return Response(
            DocumentVersionSerializer(
                list_pending_versions(), many=True, context={"storage": get_budgeted_storage()}
            ).data
        )


class CandidateDocumentsListView(APIView):
    permission_classes = [CanReviewDocuments]

    def get(self, request, candidate_pubkey):
        versions = list_candidate_versions(candidate_pubkey)
        return Response(
            DocumentVersionSerializer(
                versions, many=True, context={"storage": get_budgeted_storage(), "include_download_url": True}
            ).data
        )


class DocumentReviewView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        version = DocumentService.approve_by_pubkey(pubkey, request.user)
        return Response(
            DocumentVersionSerializer(
                version, context={"storage": get_budgeted_storage(), "include_download_url": True}
            ).data
        )


class DocumentRejectView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        serializer = DocumentRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = DocumentService.reject_by_pubkey(pubkey, request.user, serializer.validated_data["reason"])
        return Response(
            DocumentVersionSerializer(
                version, context={"storage": get_budgeted_storage(), "include_download_url": True}
            ).data
        )


class DocumentDetailView(APIView):
    permission_classes = [IsDocumentOwnerOrReviewer]

    def get(self, request, pubkey):
        version = DocumentService.get_by_pubkey(pubkey)
        self.check_object_permissions(request, version)
        return Response(
            DocumentVersionSerializer(
                version, context={"storage": get_budgeted_storage(), "include_download_url": True}
            ).data
        )