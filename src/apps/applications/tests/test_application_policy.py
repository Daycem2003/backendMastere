from types import SimpleNamespace
from unittest.mock import patch

from src.apps.applications.models import ApplicationStatus
from src.apps.applications.policies.application_policy import ApplicationPolicy


def _application(statut=ApplicationStatus.SOUMISE, candidate_user_id=1, coordinateur_user_id=2):
    return SimpleNamespace(
        statut=statut,
        candidate_profile=SimpleNamespace(user_id=candidate_user_id),
        master=SimpleNamespace(coordinateur=SimpleNamespace(user_id=coordinateur_user_id)),
    )


def test_owner_can_withdraw_while_soumise():
    app = _application(statut=ApplicationStatus.SOUMISE, candidate_user_id=1)
    user = SimpleNamespace(pk=1, pubkey="usr_1")
    assert ApplicationPolicy.can_withdraw(user, app) is True


def test_non_owner_cannot_withdraw():
    app = _application(candidate_user_id=1)
    user = SimpleNamespace(pk=2, pubkey="usr_2")
    assert ApplicationPolicy.can_withdraw(user, app) is False


def test_cannot_withdraw_already_decided_application():
    app = _application(statut=ApplicationStatus.ACCEPTEE, candidate_user_id=1)
    user = SimpleNamespace(pk=1, pubkey="usr_1")
    assert ApplicationPolicy.can_withdraw(user, app) is False


@patch("src.apps.applications.policies.application_policy.AuthorizationService")
def test_coordinator_of_the_master_can_decide(mock_authz):
    mock_authz.has_role.return_value = False
    app = _application(statut=ApplicationStatus.SOUMISE, coordinateur_user_id=5)
    user = SimpleNamespace(pk=5, pubkey="usr_5")
    assert ApplicationPolicy.can_decide(user, app) is True


@patch("src.apps.applications.policies.application_policy.AuthorizationService")
def test_unrelated_coordinator_cannot_decide(mock_authz):
    mock_authz.has_role.return_value = False
    app = _application(statut=ApplicationStatus.SOUMISE, coordinateur_user_id=5)
    user = SimpleNamespace(pk=99, pubkey="usr_99")
    assert ApplicationPolicy.can_decide(user, app) is False
