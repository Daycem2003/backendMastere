import logging
import uuid

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.candidate_profile.models import CandidateProfile
from src.apps.coordinator.models import Coordinateur
from src.apps.notifications.models import (
    BroadcastNotification,
    BroadcastTarget,
    NotificationMotif,
    NotificationRecord,
)
from src.apps.notifications.permissions.notification_permissions import CanBroadcastNotifications
from src.apps.notifications.serializers.notification import (
    BroadcastNotificationSerializer,
    CreateBroadcastNotificationSerializer,
)
from src.apps.users.models import User
from src.apps.websocket_events.emitter import notify_group, notify_user

logger = logging.getLogger(__name__)


class BroadcastNotificationView(APIView):
    """Endpoint de diffusion d'annonces de l'administrateur avec ciblage et temps réel."""

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanBroadcastNotifications()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        broadcasts = BroadcastNotification.objects.all().order_by("-envoyee_le")
        return Response(BroadcastNotificationSerializer(broadcasts, many=True).data)

    def post(self, request):
        serializer = CreateBroadcastNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cible = serializer.validated_data.get("cible", BroadcastTarget.TOUS)
        objet = serializer.validated_data["objet"]
        message = serializer.validated_data["message"]

        user = request.user if isinstance(request.user, User) else None

        broadcast = BroadcastNotification.objects.create(
            pubkey=f"bcast_{uuid.uuid4().hex[:24]}",
            cible=cible,
            objet=objet,
            message=message,
            created_by=user,
        )


        payload = {
            "pubkey": broadcast.pubkey,
            "cible": broadcast.cible,
            "objet": broadcast.objet,
            "message": broadcast.message,
            "corps": broadcast.message,
            "motif": "AUTRE",
            "envoyee_le": broadcast.envoyee_le.isoformat(),
        }

        # 1. Émission globale sur le groupe broadcast:all
        notify_group("broadcast:all", "notification:broadcast", payload)

        # 2. Persistance et émission ciblée vers les utilisateurs
        target_user_ids = set()

        if cible in (BroadcastTarget.CANDIDATS, BroadcastTarget.TOUS):
            candidates = list(
                CandidateProfile.objects.filter(
                    deleted_at__isnull=True, user_id__isnull=False
                )
            )
            # Création en lot de NotificationRecord pour que l'annonce apparaisse dans leur historique
            records_to_create = [
                NotificationRecord(
                    pubkey=f"notif_{uuid.uuid4().hex[:24]}",
                    candidate_profile=c,
                    motif=NotificationMotif.AUTRE,
                    objet=objet,
                    corps=message,
                )
                for c in candidates
            ]
            if records_to_create:
                NotificationRecord.objects.bulk_create(records_to_create)

            for c in candidates:
                if c.user_id:
                    target_user_ids.add(c.user_id)

        if cible in (BroadcastTarget.COORDINATEURS, BroadcastTarget.TOUS):
            coordinators = list(
                Coordinateur.objects.filter(
                    deleted_at__isnull=True, user_id__isnull=False
                )
            )
            for coord in coordinators:
                if coord.user_id:
                    target_user_ids.add(coord.user_id)

        if cible == BroadcastTarget.TOUS:
            all_users = User.objects.filter(is_active=True).values_list("id", flat=True)
            for uid in all_users:
                target_user_ids.add(uid)

        # 3. Notification temps réel directe vers chaque utilisateur cible connecté
        for uid in target_user_ids:
            notify_user(user_id=uid, event="notification:broadcast", payload=payload)
            notify_user(user_id=uid, event="notification:new", payload=payload)

        logger.info(
            "broadcast_notification_sent",
            extra={
                "broadcast_id": broadcast.pk,
                "cible": cible,
                "recipient_count": len(target_user_ids),
                "admin_id": request.user.pk,
            },
        )

        return Response(
            BroadcastNotificationSerializer(broadcast).data,
            status=status.HTTP_201_CREATED,
        )
