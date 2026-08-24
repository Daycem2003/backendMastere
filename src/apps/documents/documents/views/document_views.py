from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.documents.dto.document import DocumentUploadDTO
from src.apps.documents.exceptions.document_exceptions import NoCandidateProfile
from src.apps.documents.permissions.document_permissions import CanReviewDocuments
from src.apps.documents.selectors.document_selector import (
    list_candidate_versions,
    list_pending_versions,
)
from src.apps.documents.serializers.document import (
    DocumentRejectionSerializer,
    DocumentUploadSerializer,
    DocumentVersionSerializer,
)
from src.apps.documents.services.document_service import DocumentService
from src.apps.documents.services.storage import get_default_storage


def _require_candidate_profile(request):
    """FIX: lève une 403 propre au lieu de laisser passer une AttributeError
    (500) quand l'utilisateur authentifié n'a pas de profil candidat."""
    profile = getattr(request.user, "candidate_profile", None)
    if profile is None:
        raise NoCandidateProfile()
    return profile


class MyDocumentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _require_candidate_profile(request)
        versions = list_candidate_versions(profile.pubkey)
        storage = get_default_storage()
        return Response(
            DocumentVersionSerializer(versions, many=True, context={"storage": storage}).data
        )


class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = _require_candidate_profile(request)

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]

        storage = get_default_storage()
        # FIX: taille/mime/checksum calculés côté serveur à partir du
        # fichier réellement reçu, et le fichier est réellement envoyé au
        # storage backend (auparavant storage.py n'était jamais appelé).
        stored = DocumentService.store_uploaded_file(uploaded_file, profile.pubkey, storage)

        payload = DocumentUploadDTO(
            document_pubkey=serializer.validated_data.get("document_pubkey") or None,
            candidate_profile_pubkey=profile.pubkey,
            document_type=serializer.validated_data["document_type"],
            **stored,
        )
        version = DocumentService.create_version(payload, request.user)
        return Response(
            DocumentVersionSerializer(version, context={"storage": storage}).data,
            status=status.HTTP_201_CREATED,
        )


class PendingDocumentListView(APIView):
    permission_classes = [CanReviewDocuments]

    def get(self, request):
        storage = get_default_storage()
        return Response(
            DocumentVersionSerializer(
                list_pending_versions(), many=True, context={"storage": storage}
            ).data
        )


class DocumentReviewView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        version = DocumentService.approve_by_pubkey(pubkey, request.user)
        return Response(DocumentVersionSerializer(version, context={"storage": get_default_storage()}).data)


class DocumentRejectView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        serializer = DocumentRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = DocumentService.reject_by_pubkey(
            pubkey, request.user, serializer.validated_data["reason"]
        )
        return Response(DocumentVersionSerializer(version, context={"storage": get_default_storage()}).data)


class DocumentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        # FIX: cherche maintenant par DocumentVersion.pubkey (via le service,
        # qui lève DocumentVersionNotFound -> 404 géré globalement) au lieu
        # du pubkey de l'ancien modèle Document, souvent absent.
        version = DocumentService.get_by_pubkey(pubkey)
        if (
            version.candidate_profile.user_id != request.user.pk
            and not CanReviewDocuments().has_permission(request, self)
        ):
            return Response({"detail": "Accès refusé."}, status=403)
        return Response(DocumentVersionSerializer(version, context={"storage": get_default_storage()}).data)
