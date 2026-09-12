from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.notifications.dto.notification import NotifyDocumentIssueDTO
from src.apps.notifications.exceptions.notification_exceptions import NotificationNotFound
from src.apps.notifications.permissions.notification_permissions import CanSendNotifications
from src.apps.notifications.selectors.notification_selector import (
    list_for_candidate,
    unread_count_for_candidate,
)
from src.apps.notifications.serializers.notification import (
    NotificationRecordSerializer,
    NotifyDocumentIssueSerializer,
)
from src.apps.notifications.services.notification_service import NotificationService


def _require_candidate_profile(request):
    from src.apps.notifications.exceptions.notification_exceptions import (
        CandidateProfileNotFound,
    )
    from src.apps.candidate_profile.selectors.candidate_profile_selector import get_by_user

    profile = get_by_user(request.user)
    if profile is None:
        raise CandidateProfileNotFound()
    return profile



class NotifyDocumentIssueView(APIView):
    """Coordinateur/admin signale un document manquant ou frauduleux.

    `application_pubkey` est optionnel : absent quand le document concerné
    est un document de constitution de profil (le candidat n'a pas encore
    postulé), présent quand le signalement concerne une candidature.
    """

    permission_classes = [CanSendNotifications]

    def post(self, request):
        serializer = NotifyDocumentIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = NotifyDocumentIssueDTO(**serializer.validated_data)
        record = NotificationService.notify_document_issue(payload, request.user)
        return Response(
            NotificationRecordSerializer(record).data, status=status.HTTP_201_CREATED
        )


class MyNotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _require_candidate_profile(request)
        unread_only = request.query_params.get("unread") == "true"
        notifications = list_for_candidate(profile.pubkey, unread_only=unread_only)
        return Response(NotificationRecordSerializer(notifications, many=True).data)


class MyUnreadNotificationCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = _require_candidate_profile(request)
        return Response({"unread_count": unread_count_for_candidate(profile.pubkey)})


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pubkey):
        try:
            record = NotificationService.mark_as_read(pubkey, request.user)
        except NotificationNotFound:
            raise
        return Response(NotificationRecordSerializer(record).data)
