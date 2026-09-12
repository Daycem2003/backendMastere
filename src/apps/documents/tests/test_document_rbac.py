from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from src.apps.administrator.models import Administrateur
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.coordinator.models import Coordinateur
from src.apps.documents.dto.document import DocumentSlotIdentityDTO, DocumentUploadDTO
from src.apps.documents.models import DocumentReviewStatus, DocumentSlot, DocumentVersion, SlotType
from src.apps.documents.services.document_service import DocumentService
from src.apps.documents.views.document_views import (
    CandidateDocumentsListView,
    DocumentDetailView,
    DocumentRejectView,
    DocumentReviewView,
    MyDocumentListView,
    PendingDocumentListView,
)

User = get_user_model()


def make_candidate(pubkey, user, cin):
    return CandidateProfile.objects.create(
        pubkey=pubkey, user=user, nom="Nom", prenom="Prenom", cin=cin,
        email=user.email, telephone="00000000", ville="Sousse",
        annee_naissance=2000,
    )


def make_slot(pubkey, profile, slot_type=SlotType.RELEVE_LICENCE, **kwargs):
    return DocumentSlot.objects.create(
        pubkey=pubkey, candidate_profile=profile, type=slot_type, **kwargs
    )


def make_version(pubkey, slot, version_number=1, **kwargs):
    return DocumentVersion.objects.create(
        pubkey=pubkey, slot=slot, version_number=version_number,
        storage_key=kwargs.pop("storage_key", "k"),
        mime_type=kwargs.pop("mime_type", "application/pdf"),
        file_size=kwargs.pop("file_size", 100),
        **kwargs,
    )


class DocumentRBACTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        self.candidate_user = User.objects.create(pubkey="user_cand_1", email="candidate@example.com")
        self.other_candidate_user = User.objects.create(pubkey="user_cand_2", email="other@example.com")
        self.coordinator_user = User.objects.create(pubkey="user_coord_1", email="coord@example.com")
        self.admin_user = User.objects.create(pubkey="user_admin_1", email="admin@example.com")
        self.no_role_user = User.objects.create(pubkey="user_random_1", email="random@example.com")

        Coordinateur.objects.create(
            pubkey="coord_1", user=self.coordinator_user, nom="Coordinateur Test",
            email=self.coordinator_user.email,
        )
        Administrateur.objects.create(
            pubkey="admin_1", user=self.admin_user, nom="Admin Test",
            email=self.admin_user.email,
        )

        self.profile = make_candidate("cand_1", self.candidate_user, "CIN001")
        self.other_profile = make_candidate("cand_2", self.other_candidate_user, "CIN002")

        self.own_slot = make_slot("slot_1", self.profile)
        self.other_slot = make_slot("slot_2", self.other_profile)

        self.own_version = make_version("docv_1", self.own_slot, storage_key="k1")
        self.other_version = make_version("docv_2", self.other_slot, storage_key="k2")

    def _auth(self, request, user):
        force_authenticate(request, user=user)
        return request

    # --- Isolation candidat ---

    def test_candidate_sees_only_own_documents(self):
        request = self._auth(self.factory.get("/me/documents/"), self.candidate_user)
        response = MyDocumentListView.as_view()(request)
        self.assertEqual({d["pubkey"] for d in response.data}, {"docv_1"})

    def test_candidate_cannot_view_other_candidate_document(self):
        request = self._auth(self.factory.get("/x/"), self.candidate_user)
        response = DocumentDetailView.as_view()(request, pubkey=self.other_version.pubkey)
        self.assertEqual(response.status_code, 403)

    def test_candidate_can_view_own_document(self):
        request = self._auth(self.factory.get("/x/"), self.candidate_user)
        response = DocumentDetailView.as_view()(request, pubkey=self.own_version.pubkey)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["download_url"])

    def test_candidate_cannot_access_pending_queue(self):
        request = self._auth(self.factory.get("/pending/"), self.candidate_user)
        response = PendingDocumentListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_approve_document(self):
        request = self._auth(self.factory.post("/approve/"), self.candidate_user)
        response = DocumentReviewView.as_view()(request, pubkey=self.own_version.pubkey)
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_list_other_candidate_via_reviewer_endpoint(self):
        request = self._auth(self.factory.get("/x/"), self.candidate_user)
        response = CandidateDocumentsListView.as_view()(request, candidate_pubkey="cand_2")
        self.assertEqual(response.status_code, 403)

    # --- Accès global coordinateur ---

    def test_coordinator_sees_pending_documents_across_all_candidates(self):
        request = self._auth(self.factory.get("/pending/"), self.coordinator_user)
        response = PendingDocumentListView.as_view()(request)
        self.assertEqual({d["pubkey"] for d in response.data}, {"docv_1", "docv_2"})

    def test_coordinator_can_view_any_candidate_document(self):
        request = self._auth(self.factory.get("/x/"), self.coordinator_user)
        response = DocumentDetailView.as_view()(request, pubkey=self.other_version.pubkey)
        self.assertEqual(response.status_code, 200)

    def test_coordinator_can_list_any_candidate_documents(self):
        request = self._auth(self.factory.get("/x/"), self.coordinator_user)
        response = CandidateDocumentsListView.as_view()(request, candidate_pubkey="cand_2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({d["pubkey"] for d in response.data}, {"docv_2"})

    def test_coordinator_can_approve_any_candidate_document(self):
        request = self._auth(self.factory.post("/approve/"), self.coordinator_user)
        response = DocumentReviewView.as_view()(request, pubkey=self.other_version.pubkey)
        self.assertEqual(response.status_code, 200)
        self.other_version.refresh_from_db()
        self.assertEqual(self.other_version.status, DocumentReviewStatus.APPROVED)

    def test_reject_without_reason_is_rejected_with_400(self):
        request = self._auth(
            self.factory.post("/reject/", {"reason": "   "}, format="json"), self.coordinator_user
        )
        response = DocumentRejectView.as_view()(request, pubkey=self.own_version.pubkey)
        self.assertEqual(response.status_code, 400)

    def test_reject_with_reason_succeeds_and_records_it(self):
        request = self._auth(
            self.factory.post("/reject/", {"reason": "Document illisible"}, format="json"),
            self.coordinator_user,
        )
        response = DocumentRejectView.as_view()(request, pubkey=self.own_version.pubkey)
        self.assertEqual(response.status_code, 200)
        self.own_version.refresh_from_db()
        self.assertEqual(self.own_version.status, DocumentReviewStatus.REJECTED)
        self.assertEqual(self.own_version.rejection_reason, "Document illisible")

    # --- Administrateur : mêmes droits que coordinateur ---

    def test_admin_has_same_global_access_as_coordinator(self):
        request = self._auth(self.factory.get("/pending/"), self.admin_user)
        response = PendingDocumentListView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # --- Utilisateur sans rôle ---

    def test_authenticated_user_without_any_role_is_forbidden(self):
        request = self._auth(self.factory.get("/pending/"), self.no_role_user)
        response = PendingDocumentListView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_is_rejected(self):
        request = self.factory.get("/pending/")
        response = PendingDocumentListView.as_view()(request)
        self.assertIn(response.status_code, (401, 403))


class ReplacementWorkflowTests(TestCase):
    """Un rejet suivi d'un remplacement doit reproduire PENDING_REVIEW."""

    def setUp(self):
        self.user = User.objects.create(email="workflow@example.com")
        self.profile = make_candidate("cand_wf", self.user, "CINWF")

    def test_new_version_after_rejection_is_pending_review(self):
        slot = make_slot("slot_wf", self.profile, slot_type=SlotType.DIPLOME_LICENCE)
        v1 = make_version("docv_wf1", slot, storage_key="k", file_size=10)

        DocumentService.reject(v1.pk, reviewer=self.user, reason="Manquant")
        v1.refresh_from_db()
        self.assertEqual(v1.status, DocumentReviewStatus.REJECTED)

        payload = DocumentUploadDTO(
            candidate_profile_pubkey="cand_wf",
            slot=DocumentSlotIdentityDTO(slot_type=SlotType.DIPLOME_LICENCE),
            storage_key="k2", mime_type="application/pdf", file_size=20, checksum="abc",
        )
        v2 = DocumentService.create_version(payload, actor=self.user)
        self.assertEqual(v2.status, DocumentReviewStatus.PENDING_REVIEW)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v2.replaced_version_id, v1.pk)


class ApplicationEligibilityTests(TestCase):
    """Un candidat ne peut postuler que si tous les slots requis sont
    APPROVED."""

    def setUp(self):
        self.user = User.objects.create(email="elig@example.com")
        self.profile = make_candidate("cand_elig", self.user, "CINELIG")

    def test_partial_approval_blocks_application(self):
        slot = make_slot("slot_e1", self.profile, slot_type=SlotType.RELEVE_LICENCE)
        make_version("docv_e1", slot, file_size=1, status=DocumentReviewStatus.APPROVED)

        self.assertFalse(
            DocumentService.can_candidate_apply(
                self.profile.pk, [SlotType.RELEVE_LICENCE, SlotType.DIPLOME_LICENCE]
            )
        )

    def test_full_approval_allows_application(self):
        slot1 = make_slot("slot_e2", self.profile, slot_type=SlotType.RELEVE_LICENCE)
        make_version("docv_e2", slot1, file_size=1, status=DocumentReviewStatus.APPROVED)

        slot2 = make_slot("slot_e3", self.profile, slot_type=SlotType.DIPLOME_LICENCE)
        make_version("docv_e3", slot2, file_size=1, status=DocumentReviewStatus.APPROVED)

        self.assertTrue(
            DocumentService.can_candidate_apply(
                self.profile.pk, [SlotType.RELEVE_LICENCE, SlotType.DIPLOME_LICENCE]
            )
        )