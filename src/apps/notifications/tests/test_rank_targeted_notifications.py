import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.files.uploadedfile import SimpleUploadedFile

from src.apps.applications.models import Application, ApplicationStatus
from src.apps.candidate_profile.models import CandidateProfile, CandidateStatus
from src.apps.masters.models import Master
from src.apps.notifications.models import (
    BroadcastNotification,
    BroadcastTarget,
    NotificationRecord,
)
from src.apps.notifications.views.broadcast_views import (
    BroadcastNotificationView,
    NotificationAttachmentDownloadView,
    NotifyTopRankedView,
)
from src.apps.users.models import User


@pytest.mark.django_db
class TestRankTargetedNotifications:
    def test_notify_top_ranked_candidates_creates_personalized_notifications(self):
        factory = APIRequestFactory()

        # 1. Setup Admin user
        admin_user = User.objects.create(
            pubkey="usr_admin_ranked_1",
            email="admin_ranked@test.com",
            password="hash",
            is_active=True,
        )

        # 2. Setup Coordinator and Master
        from django.utils import timezone
        from src.apps.coordinator.models import Coordinateur
        coord_user = User.objects.create(pubkey="usr_coord_m1", email="coord_m1@test.com", password="h", is_active=True)
        coord = Coordinateur.objects.create(
            pubkey="coord_1", user=coord_user, nom="Dr. Salah", email="coord_m1@test.com",
        )

        now = timezone.now()
        master = Master.objects.create(
            pubkey="mst_informatique_1",
            nom="Informatique Fondamentale",
            universite="Université de Monastir",
            ville="Monastir",
            domaine="Sciences et Technologies",
            discipline="Informatique",
            specialite="Génie Logiciel",
            nombre_places=2,
            date_debut=now,
            date_fin=now + timezone.timedelta(days=30),
            statut="OUVERT",
            coordinateur=coord,
        )

        # 3. Setup Candidates & Applications
        u1 = User.objects.create(pubkey="usr_cand_1", email="c1@test.com", password="h", is_active=True)
        cp1 = CandidateProfile.objects.create(
            pubkey="prof_1", user=u1, nom="Ben Ali", prenom="Ahmed", cin="11111111",
            email="c1@test.com", telephone="99111222", ville="Monastir", annee_naissance=2000,
            statut=CandidateStatus.VALIDE,
        )
        app1 = Application.objects.create(
            pubkey="app_1", candidate_profile=cp1, master=master, niveau="M1", score=16.5, rang=1,
            statut=ApplicationStatus.SOUMISE,
        )

        u2 = User.objects.create(pubkey="usr_cand_2", email="c2@test.com", password="h", is_active=True)
        cp2 = CandidateProfile.objects.create(
            pubkey="prof_2", user=u2, nom="Trabelsi", prenom="Sarra", cin="22222222",
            email="c2@test.com", telephone="99333444", ville="Sousse", annee_naissance=2001,
            statut=CandidateStatus.VALIDE,
        )
        app2 = Application.objects.create(
            pubkey="app_2", candidate_profile=cp2, master=master, niveau="M1", score=14.0, rang=2,
            statut=ApplicationStatus.SOUMISE,
        )

        u3 = User.objects.create(pubkey="usr_cand_3", email="c3@test.com", password="h", is_active=True)
        cp3 = CandidateProfile.objects.create(
            pubkey="prof_3", user=u3, nom="Gharbi", prenom="Karim", cin="33333333",
            email="c3@test.com", telephone="99555666", ville="Tunis", annee_naissance=1999,
            statut=CandidateStatus.VALIDE,
        )
        app3 = Application.objects.create(
            pubkey="app_3", candidate_profile=cp3, master=master, niveau="M1", score=10.0, rang=3,
            statut=ApplicationStatus.SOUMISE,
        )

        # 4. Trigger top 2 notification with CSV auto-generation
        with patch("src.apps.authorization.services.authorization_service.AuthorizationService.has_role", return_value=True):
            post_request = factory.post(
                "/api/v1/notifications/notify-top-ranked",
                {
                    "master_pubkey": master.pubkey,
                    "n_premiers": 2,
                    "joindre_classement_csv": True,
                },
                format="multipart",
            )
            force_authenticate(post_request, user=admin_user)

            view = NotifyTopRankedView.as_view()
            response = view(post_request)

            assert response.status_code == 201
            assert response.data["notified_count"] == 2
            assert response.data["master_nom"] == "Informatique Fondamentale"

            # Verify personalized NotificationRecord for candidate 1
            notif1 = NotificationRecord.objects.filter(candidate_profile=cp1).first()
            assert notif1 is not None
            assert "Salut Ahmed Ben Ali" in notif1.corps
            assert "Informatique Fondamentale" in notif1.corps
            assert notif1.objet == "Appel au dépôt du dossier de candidature à l'administration de l'institut"
            assert notif1.piece_jointe_nom is not None
            assert notif1.piece_jointe_nom.endswith(".csv")

            # Verify personalized NotificationRecord for candidate 2
            notif2 = NotificationRecord.objects.filter(candidate_profile=cp2).first()
            assert notif2 is not None
            assert "Salut Sarra Trabelsi" in notif2.corps

            # Candidate 3 (rank 3) was NOT notified
            notif3 = NotificationRecord.objects.filter(candidate_profile=cp3).first()
            assert notif3 is None

            # Verify BroadcastNotification entry for audit
            bcast = BroadcastNotification.objects.filter(cible=BroadcastTarget.MASTER_RANG).first()
            assert bcast is not None
            assert bcast.master == master
            assert bcast.rang_max == 2

            # 5. Verify Attachment Download URL View
            dl_request = factory.get(f"/api/v1/notifications/{notif1.pubkey}/attachment-url")
            force_authenticate(dl_request, user=u1)
            dl_view = NotificationAttachmentDownloadView.as_view()
            dl_response = dl_view(dl_request, pubkey=notif1.pubkey)
            assert dl_response.status_code == 200
            assert "url" in dl_response.data
            assert dl_response.data["filename"] == notif1.piece_jointe_nom
