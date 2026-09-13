import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from src.apps.notifications.views.broadcast_views import BroadcastNotificationView


@pytest.mark.django_db
class TestBroadcastNotifications:
    def test_admin_can_send_and_list_broadcasts(self):
        factory = APIRequestFactory()

        # Mock Admin User
        user = MagicMock()
        user.is_authenticated = True
        user.pk = 1
        user.id = 1
        user.pubkey = "usr_admin_1"
        user.is_staff = True

        with patch("src.apps.authorization.services.authorization_service.AuthorizationService.has_role", return_value=True):
            # 1. POST broadcast
            post_request = factory.post("/api/v1/notifications/broadcast", {
                "cible": "TOUS",
                "objet": "Test Annonce",
                "message": "Message de test",
            }, format="json")
            force_authenticate(post_request, user=user)

            view = BroadcastNotificationView.as_view()
            response = view(post_request)
            assert response.status_code == 201
            assert response.data["objet"] == "Test Annonce"
            assert response.data["cible"] == "TOUS"

            # 2. GET broadcasts
            get_request = factory.get("/api/v1/notifications/broadcasts")
            force_authenticate(get_request, user=user)
            get_response = view(get_request)
            assert get_response.status_code == 200
            assert len(get_response.data) >= 1
            assert get_response.data[0]["objet"] == "Test Annonce"

    def test_coordinator_can_list_broadcast_notifications_without_candidate_profile(self):
        from src.apps.notifications.views.notification_views import MyNotificationListView
        from src.apps.notifications.models import BroadcastNotification, BroadcastTarget
        from src.apps.users.models import User

        coord_user = User.objects.create(
            pubkey="usr_coord_test_notif",
            email="coord_notif@test.com",
            password="hash",
            is_active=True,
        )

        BroadcastNotification.objects.create(
            pubkey="bcast_test_coord_1",
            cible=BroadcastTarget.COORDINATEURS,
            objet="Message aux coordinateurs",
            message="Contenu important",
        )

        factory = APIRequestFactory()
        request = factory.get("/api/v1/notifications/me")
        force_authenticate(request, user=coord_user)

        view = MyNotificationListView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["objet"] == "Message aux coordinateurs"
