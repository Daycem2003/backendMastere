from types import SimpleNamespace
from unittest.mock import patch

from src.apps.authorization.policies.master_policy import MasterPolicy
from src.apps.authorization.policies.candidate_policy import CandidatePolicy
from src.apps.authorization.policies.coordinator_policy import CoordinatorPolicy
from src.apps.authorization.services.authorization_service import AuthorizationService


def _make_user(user_id: int, role: str):
    return SimpleNamespace(id=user_id, pubkey=f"usr_{user_id}", role=role)


def _has_role(user_pubkey: str, role_code: str) -> bool:
    return role_code == {"usr_99": "ADMIN", "usr_1": "COORDINATOR", "usr_10": "COORDINATOR"}.get(user_pubkey)


role_check = patch.object(AuthorizationService, "has_role", side_effect=_has_role)


class TestMasterPolicy:
    def setup_method(self):
        role_check.start()

    def teardown_method(self):
        role_check.stop()
    def test_admin_can_update_any_master(self):
        admin = _make_user(user_id=99, role="ADMIN")
        assert MasterPolicy.can_update(admin, owner_user_id=1) is True

    def test_coordinator_can_update_own_master(self):
        coordinator = _make_user(user_id=1, role="COORDINATOR")
        assert MasterPolicy.can_update(coordinator, owner_user_id=1) is True

    def test_coordinator_cannot_update_others_master(self):
        coordinator = _make_user(user_id=2, role="COORDINATOR")
        assert MasterPolicy.can_update(coordinator, owner_user_id=1) is False

    def test_candidate_cannot_create_master(self):
        candidate = _make_user(user_id=3, role="CANDIDATE")
        assert MasterPolicy.can_create(candidate) is False

    def test_draft_master_hidden_from_non_owner(self):
        other_coordinator = _make_user(user_id=2, role="COORDINATOR")
        assert (
            MasterPolicy.can_view(other_coordinator, owner_user_id=1, master_status="BROUILLON")
            is False
        )

    def test_open_master_visible_to_anonymous(self):
        assert MasterPolicy.can_view(None, owner_user_id=1, master_status="OUVERT") is True


class TestCandidatePolicy:
    def setup_method(self):
        role_check.start()

    def teardown_method(self):
        role_check.stop()
    def test_owner_can_update_own_profile(self):
        candidate = _make_user(user_id=5, role="CANDIDATE")
        assert CandidatePolicy.can_update(candidate, profile_user_id=5) is True

    def test_other_candidate_cannot_update_profile(self):
        candidate = _make_user(user_id=6, role="CANDIDATE")
        assert CandidatePolicy.can_update(candidate, profile_user_id=5) is False


class TestCoordinatorPolicy:
    def setup_method(self):
        role_check.start()

    def teardown_method(self):
        role_check.stop()
    def test_coordinator_can_review_own_master_applications(self):
        coordinator = _make_user(user_id=10, role="COORDINATOR")
        assert CoordinatorPolicy.can_review_application(coordinator, master_coordinateur_user_id=10) is True

    def test_coordinator_cannot_review_others_master_applications(self):
        coordinator = _make_user(user_id=11, role="COORDINATOR")
        assert CoordinatorPolicy.can_review_application(coordinator, master_coordinateur_user_id=10) is False
