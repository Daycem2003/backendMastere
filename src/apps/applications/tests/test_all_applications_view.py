import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIRequestFactory, force_authenticate
from src.apps.applications.views.application_views import AllApplicationListView


@pytest.mark.django_db
class TestAllApplicationListView:
    def test_all_applications_view_returns_applications(self):
        factory = APIRequestFactory()
        request = factory.get("/api/v1/applications/all")

        # Mock user as ADMIN
        user = MagicMock()
        user.is_authenticated = True
        user.pubkey = "usr_admin"
        force_authenticate(request, user=user)

        with patch("src.apps.authorization.services.authorization_service.AuthorizationService.has_role", return_value=True):
            with patch("src.apps.applications.views.application_views.list_all", return_value=[]):
                view = AllApplicationListView.as_view()
                response = view(request)
                assert response.status_code == 200
                assert response.data == []

