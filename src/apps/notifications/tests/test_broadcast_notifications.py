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
