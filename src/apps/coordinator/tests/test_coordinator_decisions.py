import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from datetime import timedelta
from django.utils import timezone

from src.apps.candidate_profile.models import CandidateStatus
from src.apps.coordinator.services.coordinator_decision_service import CoordinatorDecisionService
from src.apps.authentication.services.account_activation_service import AccountActivationService
from src.apps.notifications.services.email_notification_service import EmailNotificationService


@pytest.mark.django_db
def test_coordinator_approve_candidature():
    profile = SimpleNamespace(
        id=1,
        pubkey="cand_123",
        statut=CandidateStatus.EN_ATTENTE,
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
        user=None,
        onboarding_token="token_onboard_123",
        save=MagicMock(),
    )
    user_created = SimpleNamespace(
        pk=10,
        id=10,
        pubkey="usr_123",
        email="candidat@test.tn",
        is_active=True,
        save=MagicMock(),
    )
    activation_record = SimpleNamespace(
        token="act_token_xyz_456",
        expires_at=timezone.now() + timedelta(hours=48),
        used_at=None,
    )

    with patch("src.apps.coordinator.services.coordinator_decision_service.get_by_pubkey", return_value=profile), \
         patch("src.apps.coordinator.services.coordinator_decision_service.User.objects.filter") as mock_user_filter, \
         patch("src.apps.coordinator.services.coordinator_decision_service.UserProvisioningService.create_user_with_role", return_value=user_created) as mock_create_user, \
         patch("src.apps.coordinator.services.coordinator_decision_service.AccountActivationService.create_activation_token", return_value=activation_record) as mock_create_token, \
         patch("src.apps.coordinator.services.coordinator_decision_service.EmailNotificationService.notify_candidate_approved") as mock_email_approved, \
         patch("src.apps.coordinator.services.coordinator_decision_service.NotificationRecord.objects.create") as mock_notif_create:

        mock_user_filter.return_value.first.return_value = None

        actor = SimpleNamespace(pk=99, pubkey="usr_coord", is_authenticated=True)
        res = CoordinatorDecisionService.approve_candidature(pubkey="cand_123", actor_user=actor)

        assert res.statut == CandidateStatus.VALIDE
        assert res.user == user_created
        assert profile.save.called
        mock_create_user.assert_called_once()
        mock_create_token.assert_called_once_with(user_created)
        mock_email_approved.assert_called_once_with(candidate_profile=profile, activation_token="act_token_xyz_456")
        mock_notif_create.assert_called_once()


@pytest.mark.django_db
def test_coordinator_reject_candidature():
    profile = SimpleNamespace(
        id=1,
        pubkey="cand_123",
        statut=CandidateStatus.EN_ATTENTE,
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
        save=MagicMock(),
    )

    with patch("src.apps.coordinator.services.coordinator_decision_service.get_by_pubkey", return_value=profile), \
         patch("src.apps.coordinator.services.coordinator_decision_service.EmailNotificationService.notify_candidate_rejected") as mock_email_rejected, \
         patch("src.apps.coordinator.services.coordinator_decision_service.NotificationRecord.objects.create") as mock_notif_create:

        actor = SimpleNamespace(pk=99, pubkey="usr_coord", is_authenticated=True)
        res = CoordinatorDecisionService.reject_candidature(pubkey="cand_123", motif="Dossier incomplet", actor_user=actor)

        assert res.statut == CandidateStatus.REJETE
        assert profile.save.called
        mock_email_rejected.assert_called_once_with(candidate_profile=profile, motif="Dossier incomplet")
        mock_notif_create.assert_called_once()


@pytest.mark.django_db
def test_coordinator_request_revision():
    profile = SimpleNamespace(
        id=1,
        pubkey="cand_123",
        statut=CandidateStatus.EN_ATTENTE,
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
        onboarding_token="token_onboard_123",
        latest_revision_message=None,
        save=MagicMock(),
    )

    with patch("src.apps.coordinator.services.coordinator_decision_service.get_by_pubkey", return_value=profile), \
         patch("src.apps.coordinator.services.coordinator_decision_service.DocumentSlot.objects.filter", return_value=[]), \
         patch("src.apps.coordinator.services.coordinator_decision_service.EmailNotificationService.notify_candidate_revision_needed") as mock_email_revision, \
         patch("src.apps.coordinator.services.coordinator_decision_service.NotificationRecord.objects.create") as mock_notif_create:

        actor = SimpleNamespace(pk=99, pubkey="usr_coord", is_authenticated=True)
        res = CoordinatorDecisionService.request_revision(
            pubkey="cand_123",
            message="Merci de re-scanner le diplome du bac",
            actor_user=actor,
        )

        assert res.statut == CandidateStatus.A_REVISER
        assert profile.latest_revision_message == "Merci de re-scanner le diplome du bac"
        assert profile.save.called
        mock_email_revision.assert_called_once_with(
            candidate_profile=profile,
            message="Merci de re-scanner le diplome du bac",
            onboarding_token="token_onboard_123",
            targeted_documents=[],
        )
        mock_notif_create.assert_called_once()


@pytest.mark.django_db
def test_coordinator_request_revision_with_targeted_documents():
    profile = SimpleNamespace(
        id=1,
        pubkey="cand_123",
        statut=CandidateStatus.EN_ATTENTE,
        email="candidat@test.tn",
        nom="Ben Salah",
        prenom="Ali",
        onboarding_token="token_onboard_123",
        latest_revision_message=None,
        save=MagicMock(),
    )

    mock_version = SimpleNamespace(
        pubkey="docv_1",
        status="PENDING_REVIEW",
        rejection_reason=None,
        save=MagicMock(),
    )
    mock_slot = SimpleNamespace(
        pubkey="slot_releve_l2",
        type="RELEVE_LICENCE",
        domaine="Informatique",
        annee_licence="A2",
        redoublement_annee="",
        justificatif_index=0,
        a_redeposer=False,
        save=MagicMock(),
    )

    with patch("src.apps.coordinator.services.coordinator_decision_service.get_by_pubkey", return_value=profile), \
         patch("src.apps.coordinator.services.coordinator_decision_service.DocumentSlot.objects.filter", return_value=[mock_slot]), \
         patch("src.apps.coordinator.services.coordinator_decision_service.DocumentVersion.objects.filter") as mock_version_filter, \
         patch("src.apps.coordinator.services.coordinator_decision_service.EmailNotificationService.notify_candidate_revision_needed") as mock_email_revision, \
         patch("src.apps.coordinator.services.coordinator_decision_service.NotificationRecord.objects.create") as mock_notif_create:

        mock_version_filter.return_value.first.return_value = mock_version

        actor = SimpleNamespace(pk=99, pubkey="usr_coord", is_authenticated=True)
        res = CoordinatorDecisionService.request_revision(
            pubkey="cand_123",
            message="Relevé L2 illisible",
            documents_a_redeposer=["slot_releve_l2"],
            actor_user=actor,
        )

        assert res.statut == CandidateStatus.A_REVISER
        assert mock_slot.a_redeposer is True
        assert mock_slot.save.called
        assert mock_version.status == "REJECTED"
        assert mock_version.rejection_reason == "Relevé L2 illisible"
        assert mock_version.save.called
        mock_email_revision.assert_called_once_with(
            candidate_profile=profile,
            message="Relevé L2 illisible",
            onboarding_token="token_onboard_123",
            targeted_documents=["Relevé de notes — Informatique A2"],
        )
        mock_notif_create.assert_called_once()

