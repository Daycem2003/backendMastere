import csv
import io
import logging
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.applications.models import Application
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.coordinator.models import Coordinateur
from src.apps.documents.services.storage import get_default_storage
from src.apps.masters.models import Master
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
    NotifyTopRankedSerializer,
)
from src.apps.users.models import User
from src.apps.websocket_events.emitter import notify_group, notify_user

logger = logging.getLogger(__name__)


class BroadcastNotificationView(APIView):
    """Endpoint de diffusion d'annonces de l'administrateur avec ciblage et temps réel."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]
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
        master_pubkey = serializer.validated_data.get("master_pubkey")
        rang_max = serializer.validated_data.get("rang_max")

        user = request.user if isinstance(request.user, User) else None
        broadcast_pubkey = f"bcast_{uuid.uuid4().hex[:24]}"

        # Traitement optionnel de la pièce jointe
        piece_jointe_cle = None
        piece_jointe_nom = None
        piece_jointe = request.FILES.get("piece_jointe") or serializer.validated_data.get("piece_jointe")
        if piece_jointe:
            storage = get_default_storage()
            piece_jointe_cle = f"notifications/broadcasts/{broadcast_pubkey}/{piece_jointe.name}"
            storage.upload(piece_jointe, piece_jointe_cle)
            piece_jointe_nom = piece_jointe.name

        master_obj = None
        if master_pubkey:
            master_obj = Master.objects.filter(pubkey=master_pubkey).first()

        broadcast = BroadcastNotification.objects.create(
            pubkey=broadcast_pubkey,
            cible=cible,
            master=master_obj,
            rang_max=rang_max,
            objet=objet,
            message=message,
            piece_jointe_cle=piece_jointe_cle,
            piece_jointe_nom=piece_jointe_nom,
            created_by=user,
        )

        payload = {
            "pubkey": broadcast.pubkey,
            "cible": broadcast.cible,
            "objet": broadcast.objet,
            "message": broadcast.message,
            "corps": broadcast.message,
            "motif": "AUTRE",
            "piece_jointe_nom": broadcast.piece_jointe_nom,
            "envoyee_le": broadcast.envoyee_le.isoformat(),
        }

        # 1. Émission sur les groupes WebSocket correspondants
        if cible == BroadcastTarget.TOUS:
            notify_group("broadcast:all", "notification:broadcast", payload)
            notify_group("broadcast:all", "notification:new", payload)
        elif cible == BroadcastTarget.COORDINATEURS:
            notify_group("role:coordinateur", "notification:broadcast", payload)
            notify_group("role:coordinateur", "notification:new", payload)
            notify_group("role:COORDINATEURS", "notification:broadcast", payload)
            notify_group("role:COORDINATEURS", "notification:new", payload)
        elif cible == BroadcastTarget.CANDIDATS:
            notify_group("role:candidat", "notification:broadcast", payload)
            notify_group("role:candidat", "notification:new", payload)
            notify_group("role:CANDIDATS", "notification:broadcast", payload)
            notify_group("role:CANDIDATS", "notification:new", payload)

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
                    piece_jointe_cle=piece_jointe_cle,
                    piece_jointe_nom=piece_jointe_nom,
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


class NotifyTopRankedView(APIView):
    """Notification ciblée sur les N premiers candidats d'un classement pour un Master donné.

    Chaque candidat sélectionné reçoit une notification personnalisée :
    Objet : 'Appel au dépôt du dossier de candidature à l'administration de l'institut'
    Corps : 'Salut {prenom} {nom}, vous avez été sélectionné(e) pour la présélection finale pour le Master {nom_du_master}. Veuillez respecter les délais.'
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [CanBroadcastNotifications]

    def post(self, request):
        serializer = NotifyTopRankedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        master_pubkey = serializer.validated_data["master_pubkey"]
        n_premiers = serializer.validated_data["n_premiers"]
        objet = serializer.validated_data.get(
            "objet",
            "Appel au dépôt du dossier de candidature à l'administration de l'institut",
        )
        piece_jointe = request.FILES.get("piece_jointe") or serializer.validated_data.get("piece_jointe")
        joindre_classement_csv = serializer.validated_data.get("joindre_classement_csv", False)

        try:
            master = Master.objects.get(pubkey=master_pubkey)
        except Master.DoesNotExist:
            return Response({"detail": "Master non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Récupération des N candidatures les mieux classées (rang croissant / score décroissant)
        applications = list(
            Application.objects.filter(master=master, deleted_at__isnull=True)
            .select_related("candidate_profile", "candidate_profile__user", "master")
            .order_by("rang", "-score")[:n_premiers]
        )

        if not applications:
            return Response(
                {"detail": "Aucune candidature trouvée pour ce Master."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        broadcast_pubkey = f"bcast_{uuid.uuid4().hex[:24]}"
        storage = get_default_storage()
        piece_jointe_cle = None
        piece_jointe_nom = None

        # 2. Gestion de la pièce jointe (fichier uploadé ou CSV généré automatiquement)
        if piece_jointe:
            piece_jointe_cle = f"notifications/broadcasts/{broadcast_pubkey}/{piece_jointe.name}"
            storage.upload(piece_jointe, piece_jointe_cle)
            piece_jointe_nom = piece_jointe.name
        elif joindre_classement_csv:
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer, delimiter=";")
            writer.writerow(["Rang", "Nom", "Prenom", "CIN", "Email", "Score", "Decision"])

            places = master.nombre_places or 0
            for idx, app in enumerate(applications):
                cp = app.candidate_profile
                rang = app.rang or (idx + 1)
                decision = "Principale" if rang <= places else "Liste d'attente"
                writer.writerow([
                    rang,
                    cp.nom if cp else "",
                    cp.prenom if cp else "",
                    cp.cin if cp else "",
                    cp.email if cp else "",
                    f"{app.score:.2f}" if app.score is not None else "0.00",
                    decision,
                ])

            csv_content = ("\ufeff" + csv_buffer.getvalue()).encode("utf-8")
            safe_master_name = "".join(c for c in master.nom if c.isalnum() or c in ("_", "-"))
            csv_filename = f"classement_{safe_master_name[:30]}_{uuid.uuid4().hex[:6]}.csv"
            csv_file = SimpleUploadedFile(csv_filename, csv_content, content_type="text/csv")

            piece_jointe_cle = f"notifications/broadcasts/{broadcast_pubkey}/{csv_filename}"
            storage.upload(csv_file, piece_jointe_cle)
            piece_jointe_nom = csv_filename

        # 3. Création de l'enregistrement Broadcast pour audit & historique
        user = request.user if isinstance(request.user, User) else None
        broadcast = BroadcastNotification.objects.create(
            pubkey=broadcast_pubkey,
            cible=BroadcastTarget.MASTER_RANG,
            master=master,
            rang_max=n_premiers,
            objet=objet,
            message=f"Sélection des {len(applications)} premiers candidats pour le Master {master.nom}",
            piece_jointe_cle=piece_jointe_cle,
            piece_jointe_nom=piece_jointe_nom,
            created_by=user,
        )

        # 4. Création des notifications individuelles personnalisées et émission temps réel
        created_records = []
        for app in applications:
            cp = app.candidate_profile
            if not cp:
                continue

            prenom = cp.prenom
            nom = cp.nom
            nom_du_master = master.nom
            corps = (
                f"Salut {prenom} {nom}, vous avez été sélectionné(e) pour la présélection finale "
                f"pour le Master {nom_du_master}. Veuillez respecter les délais."
            )

            record = NotificationRecord.objects.create(
                pubkey=f"notif_{uuid.uuid4().hex[:24]}",
                candidate_profile=cp,
                application=app,
                motif=NotificationMotif.CANDIDATURE_STATUT,
                objet=objet,
                corps=corps,
                piece_jointe_cle=piece_jointe_cle,
                piece_jointe_nom=piece_jointe_nom,
            )
            created_records.append(record)

            # Émission temps réel WebSocket vers le compte du candidat
            if cp.user_id:
                ws_payload = {
                    "pubkey": record.pubkey,
                    "motif": record.motif,
                    "objet": record.objet,
                    "corps": record.corps,
                    "message": record.corps,
                    "piece_jointe_nom": record.piece_jointe_nom,
                    "application_pubkey": app.pubkey,
                    "envoyee_le": record.envoyee_le.isoformat(),
                }
                notify_user(user_id=cp.user_id, event="notification:new", payload=ws_payload)

        logger.info(
            "top_ranked_notifications_sent",
            extra={
                "master_pubkey": master_pubkey,
                "n_premiers": n_premiers,
                "notified_count": len(created_records),
                "admin_id": request.user.pk,
            },
        )

        return Response(
            {
                "broadcast": BroadcastNotificationSerializer(broadcast).data,
                "notified_count": len(created_records),
                "master_nom": master.nom,
                "candidates": [
                    {
                        "nom": a.candidate_profile.nom if a.candidate_profile else "",
                        "prenom": a.candidate_profile.prenom if a.candidate_profile else "",
                        "cin": a.candidate_profile.cin if a.candidate_profile else "",
                        "rang": a.rang or (idx + 1),
                        "score": a.score,
                    }
                    for idx, a in enumerate(applications)
                ],
            },
            status=status.HTTP_201_CREATED,
        )


class NotificationAttachmentDownloadView(APIView):
    """Génère une URL pré-signée sécurisée pour télécharger la pièce jointe d'une notification."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        # Recherche dans NotificationRecord
        record = NotificationRecord.objects.filter(pubkey=pubkey, deleted_at__isnull=True).first()
        if record and record.piece_jointe_cle:
            storage = get_default_storage()
            url = storage.signed_url(record.piece_jointe_cle, expires_in=3600)
            return Response({"url": url, "filename": record.piece_jointe_nom})

        # Recherche dans BroadcastNotification
        broadcast = BroadcastNotification.objects.filter(pubkey=pubkey).first()
        if broadcast and broadcast.piece_jointe_cle:
            storage = get_default_storage()
            url = storage.signed_url(broadcast.piece_jointe_cle, expires_in=3600)
            return Response({"url": url, "filename": broadcast.piece_jointe_nom})

        return Response(
            {"detail": "Aucune pièce jointe trouvée pour cette notification."},
            status=status.HTTP_404_NOT_FOUND,
        )

