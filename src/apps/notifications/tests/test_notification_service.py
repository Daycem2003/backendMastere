"""Tests ciblant la logique métier clé du module :
- application_pubkey absent -> notification liée seulement au profil
- application_pubkey présent mais n'appartenant pas au candidat -> rejeté
- l'event websocket est bien émis via EventPublisherProtocol (WebsocketEventPublisher par défaut ou injecté)
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.apps.notifications.adapters.websocket_publisher import WebsocketEventPublisher
from src.apps.notifications.dto.notification import NotifyDocumentIssueDTO
from src.apps.notifications.exceptions.notification_exceptions import (
    ApplicationDoesNotBelongToCandidate,
    ApplicationNotFound,
    CandidateProfileNotFound,
)
from src.apps.notifications.models import NotificationMotif
from src.apps.notifications.services.notification_service import (
    NOTIFICATION_CREATED_EVENT,
    NotificationService,
)


def _dto(**overrides):
    base = dict(
        candidate_profile_pubkey="cand_1",
        application_pubkey=None,
        motif=NotificationMotif.DOCUMENT_MANQUANT,
        document_concerne="DIPLOME",
        objet="Document manquant",
        corps="Merci de soumettre votre diplôme.",
    )
    base.update(overrides)
    return NotifyDocumentIssueDTO(**base)


def _fake_candidate(user_id=42, pk=1):
    return SimpleNamespace(pubkey="cand_1", user_id=user_id, id=pk)


@patch("src.apps.websocket_events.emitter.notify_user")
@patch("src.apps.notifications.services.notification_service.NotificationRecord")
@patch("src.apps.notifications.services.notification_service.CandidateProfile")
def test_notify_without_application_creates_profile_level_notification(
    mock_candidate_cls, mock_record_cls, mock_notify_user
):
    candidate = _fake_candidate()
    mock_candidate_cls.objects.filter.return_value.first.return_value = candidate
    created = SimpleNamespace(
        pk=1,
        pubkey="notif_x",
        candidate_profile=candidate,
        application=None,
        motif="DOCUMENT_MANQUANT",
        document_concerne="DIPLOME",
        objet="o",
        corps="c",
        envoyee_le=SimpleNamespace(isoformat=lambda: "2026-08-24T00:00:00"),
    )
    mock_record_cls.objects.create.return_value = created

    result = NotificationService.notify_document_issue(_dto(), actor=SimpleNamespace(pk=99))

    assert result.application is None
    mock_notify_user.assert_called_once()
    call = mock_notify_user.call_args.kwargs
    assert call["user_id"] == candidate.user_id
    assert call["event"] == NOTIFICATION_CREATED_EVENT
    assert call["payload"]["application_pubkey"] is None


@patch("src.apps.notifications.services.notification_service.NotificationRecord")
@patch("src.apps.notifications.services.notification_service.CandidateProfile")
def test_notify_with_injected_publisher(mock_candidate_cls, mock_record_cls):
    candidate = _fake_candidate()
    mock_candidate_cls.objects.filter.return_value.first.return_value = candidate
    created = SimpleNamespace(
        pk=1,
        pubkey="notif_injected",
        candidate_profile=candidate,
        application=None,
        motif="DOCUMENT_MANQUANT",
        document_concerne="DIPLOME",
        objet="o",
        corps="c",
        envoyee_le=SimpleNamespace(isoformat=lambda: "2026-08-24T00:00:00"),
    )
    mock_record_cls.objects.create.return_value = created
    fake_publisher = MagicMock()

    result = NotificationService.notify_document_issue(
        _dto(), actor=SimpleNamespace(pk=99), event_publisher=fake_publisher
    )

    assert result.pubkey == "notif_injected"
    fake_publisher.publish.assert_called_once_with(
        user_id=candidate.user_id,
        event=NOTIFICATION_CREATED_EVENT,
        payload={
            "notification_pubkey": "notif_injected",
            "motif": "DOCUMENT_MANQUANT",
            "document_concerne": "DIPLOME",
            "objet": "o",
            "corps": "c",
            "application_pubkey": None,
            "envoyee_le": "2026-08-24T00:00:00",
        },
    )


@patch("src.apps.websocket_events.emitter.notify_user")
def test_websocket_publisher_adapter_delegates_to_emitter(mock_notify_user):
    mock_notify_user.return_value = True
    publisher = WebsocketEventPublisher()
    success = publisher.publish(user_id=10, event="notification:new", payload={"test": 1})

    assert success is True
    mock_notify_user.assert_called_once_with(
        user_id=10, event="notification:new", payload={"test": 1}
    )


@patch("src.apps.notifications.services.notification_service.CandidateProfile")
def test_notify_raises_when_candidate_profile_missing(mock_candidate_cls):
    mock_candidate_cls.objects.filter.return_value.first.return_value = None
    with pytest.raises(CandidateProfileNotFound):
        NotificationService.notify_document_issue(_dto(), actor=SimpleNamespace(pk=99))


@patch("src.apps.notifications.services.notification_service.Application")
@patch("src.apps.notifications.services.notification_service.CandidateProfile")
def test_notify_raises_when_application_pubkey_unknown(mock_candidate_cls, mock_application_cls):
    mock_candidate_cls.objects.filter.return_value.first.return_value = _fake_candidate()
    mock_application_cls.objects.filter.return_value.first.return_value = None
    with pytest.raises(ApplicationNotFound):
        NotificationService.notify_document_issue(
            _dto(application_pubkey="app_1"), actor=SimpleNamespace(pk=99)
        )


@patch("src.apps.notifications.services.notification_service.Application")
@patch("src.apps.notifications.services.notification_service.CandidateProfile")
def test_notify_raises_when_application_belongs_to_another_candidate(
    mock_candidate_cls, mock_application_cls
):
    candidate = _fake_candidate(pk=1)
    other_application = SimpleNamespace(pubkey="app_1", candidate_profile_id=999)
    mock_candidate_cls.objects.filter.return_value.first.return_value = candidate
    mock_application_cls.objects.filter.return_value.first.return_value = other_application

    with pytest.raises(ApplicationDoesNotBelongToCandidate):
        NotificationService.notify_document_issue(
            _dto(application_pubkey="app_1"), actor=SimpleNamespace(pk=99)
        )
