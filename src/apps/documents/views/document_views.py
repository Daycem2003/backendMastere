from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.documents.dto.document import DocumentUploadDTO
from src.apps.documents.models import DocumentReviewStatus
from src.apps.documents.permissions.document_permissions import CanReviewDocuments
from src.apps.documents.selectors.document_selector import (
    get_version_by_pubkey,
    list_candidate_versions,
    list_pending_versions,
)
from src.apps.documents.serializers.document import (
    DocumentRejectionSerializer,
    DocumentUploadSerializer,
    DocumentVersionSerializer,
)
from src.apps.documents.services.document_service import DocumentService


class MyDocumentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        versions = list_candidate_versions(request.user.candidate_profile.pubkey)
        return Response(DocumentVersionSerializer(versions, many=True).data)


class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = request.user.candidate_profile
        payload = DocumentUploadDTO(
            candidate_profile_pubkey=profile.pubkey,
            **serializer.validated_data,
        )
        version = DocumentService.create_version(payload, request.user)
        return Response(DocumentVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class PendingDocumentListView(APIView):
    permission_classes = [CanReviewDocuments]

    def get(self, request):
        return Response(
            DocumentVersionSerializer(list_pending_versions(), many=True).data
        )


class DocumentReviewView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        version = DocumentService.approve_by_pubkey(pubkey, request.user)
        return Response(DocumentVersionSerializer(version).data)


class DocumentRejectView(APIView):
    permission_classes = [CanReviewDocuments]

    def post(self, request, pubkey):
        serializer = DocumentRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = DocumentService.reject_by_pubkey(
            pubkey, request.user, serializer.validated_data["reason"]
        )
        return Response(DocumentVersionSerializer(version).data)


class DocumentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        version = get_version_by_pubkey(pubkey)
        if not version:
            return Response({"detail": "Document introuvable."}, status=404)
        if (
            version.candidate_profile.user_id != request.user.pk
            and not CanReviewDocuments().has_permission(request, self)
        ):
            return Response({"detail": "Accès refusé."}, status=403)
        return Response(DocumentVersionSerializer(version).data)
