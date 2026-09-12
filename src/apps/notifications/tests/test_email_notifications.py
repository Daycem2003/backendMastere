from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from src.apps.notifications.services.email_notification_service import EmailNotificationService


def test_notify_candidate_approved_sends_email():
    profile = SimpleNamespace(
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
    )
    with patch("src.apps.notifications.services.email_notification_service.EmailMultiAlternatives") as mock_email_cls:
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        success = EmailNotificationService.notify_candidate_approved(profile, "token_123")

        assert success is True
        mock_email_cls.assert_called_once()
        mock_msg.attach_alternative.assert_called_once()
        mock_msg.send.assert_called_once_with(fail_silently=False)


def test_notify_candidate_rejected_sends_email():
    profile = SimpleNamespace(
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
    )
    with patch("src.apps.notifications.services.email_notification_service.EmailMultiAlternatives") as mock_email_cls:
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        success = EmailNotificationService.notify_candidate_rejected(profile, "Dossier incomplet")

        assert success is True
        mock_email_cls.assert_called_once()
        mock_msg.send.assert_called_once()


def test_notify_candidate_revision_needed_sends_email():
    profile = SimpleNamespace(
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
    )
    with patch("src.apps.notifications.services.email_notification_service.EmailMultiAlternatives") as mock_email_cls:
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg

        success = EmailNotificationService.notify_candidate_revision_needed(
            profile, "Revoir le diplôme", "onboard_token_123"
        )

        assert success is True
        mock_email_cls.assert_called_once()
        mock_msg.send.assert_called_once()
