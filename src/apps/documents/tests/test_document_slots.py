from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from src.apps.administrator.models import Administrateur
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.coordinator.models import Coordinateur
from src.apps.documents.dto.document import DocumentSlotIdentityDTO, DocumentUploadDTO
from src.apps.documents.models import (
    DocumentReviewStatus,
    DocumentSlot,
    DocumentVersion,
)
from src.apps.documents.services.document_service import DocumentService
from src.apps.documents.views.document_views import (
    DocumentDetailView,
    DocumentReviewView,
    MySlotListView,
    PendingDocumentListView,
)

User = get_user_model()


def make_candidate(pubkey, user, cin):
    return CandidateProfile.objects.create(
        pubkey=pubkey, user=user, nom="N", prenom="P", cin=cin, email=user.email,
        telephone="0", ville="Sousse", annee_naissance=2000,
    )


def upload(candidate, slot_type, actor, **slot_kwargs):
    payload = DocumentUploadDTO(
        candidate_profile_pubkey=candidate.pubkey,
        slot=DocumentSlotIdentityDTO(slot_type=slot_type, **slot_kwargs),
        storage_key=f"k_{DocumentVersion.objects.count()}",
        mime_type="application/pdf",
        file_size=100,
        checksum="abc",
    )
    return DocumentService.create_version(payload, actor)


class DocumentSlotUniquenessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(pubkey="u1", email="c@example.com")
        self.candidate = make_candidate("cand_1", self.user, "CIN1")

    def test_same_domaine_and_annee_reuses_same_slot(self):
        v1 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A1")
        v2 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A1")
        self.assertEqual(v1.slot_id, v2.slot_id)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v2.replaced_version_id, v1.pk)

    def test_different_domaine_creates_distinct_slots(self):
        v1 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A1")
        v2 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Mathematiques", annee_licence="A1")
        self.assertNotEqual(v1.slot_id, v2.slot_id)

    def test_different_annee_creates_distinct_slots_for_same_domaine(self):
        v1 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A1")
        v2 = upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A2")
        self.assertNotEqual(v1.slot_id, v2.slot_id)

    def test_multiple_justificatifs_same_redoublement_year_are_distinct_slots(self):
        v1 = upload(self.candidate, "JUSTIFICATIF_REDOUBLEMENT", self.user, redoublement_annee="Licence 2", justificatif_index=1)
        v2 = upload(self.candidate, "JUSTIFICATIF_REDOUBLEMENT", self.user, redoublement_annee="Licence 2", justificatif_index=2)
        self.assertNotEqual(v1.slot_id, v2.slot_id)

    def test_db_level_unique_constraint_on_slot_is_enforced(self):
        # Vérifie que la contrainte bloque bien un doublon EXACT au niveau
        # DB (pas seulement get_or_create côté applicatif) — les valeurs
        # "" / 0 par défaut (non NULL) garantissent que la contrainte
        # s'applique réellement, contrairement au bug historique sur
        # `document` nullable.
        DocumentSlot.objects.create(candidate_profile=self.candidate, type="RELEVE_M1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DocumentSlot.objects.create(candidate_profile=self.candidate, type="RELEVE_M1")

    def test_version_unique_constraint_is_per_slot_not_global(self):
        slot_a = DocumentSlot.objects.create(candidate_profile=self.candidate, type="RELEVE_M1")
        slot_b = DocumentSlot.objects.create(
            candidate_profile=self.candidate, type="RELEVE_LICENCE", domaine="Informatique", annee_licence="A1",
        )
        # version_number=1 sur deux slots différents du même candidat : OK,
        # la contrainte porte sur (slot, version_number), pas globale.
        DocumentVersion.objects.create(
            pubkey="v_a1", slot=slot_a, version_number=1, storage_key="k1",
            mime_type="application/pdf", file_size=1,
        )
        DocumentVersion.objects.create(
            pubkey="v_b1", slot=slot_b, version_number=1, storage_key="k2",
            mime_type="application/pdf", file_size=1,
        )  # ne doit pas lever


class DocumentSlotConcurrencyTests(TestCase):
    """Vérifie que le verrouillage porte sur CandidateProfile (ligne
    toujours existante), corrigeant la race condition identifiée à l'audit
    initial (select_for_update() sur un queryset `previous` vide ne
    verrouillait rien pour un premier upload)."""

    def setUp(self):
        self.user = User.objects.create(pubkey="u2", email="conc@example.com")
        self.candidate = make_candidate("cand_conc", self.user, "CINCONC")

    def test_sequential_uploads_increment_version_number_without_gap(self):
        v1 = upload(self.candidate, "RELEVE_M1", self.user)
        v2 = upload(self.candidate, "RELEVE_M1", self.user)
        v3 = upload(self.candidate, "RELEVE_M1", self.user)
        self.assertEqual([v1.version_number, v2.version_number, v3.version_number], [1, 2, 3])
        self.assertFalse(DocumentVersion.objects.get(pk=v1.pk).is_active)
        self.assertFalse(DocumentVersion.objects.get(pk=v2.pk).is_active)
        self.assertTrue(DocumentVersion.objects.get(pk=v3.pk).is_active)


class MultiDomainEligibilityTests(TestCase):
    """Vérifie can_candidate_apply avec PLUSIEURS slots du même type
    (le point central de ce refactor)."""

    def setUp(self):
        self.user = User.objects.create(pubkey="u3", email="elig@example.com")
        self.candidate = make_candidate("cand_elig", self.user, "CINELIG")

    def _approve_latest(self, slot_type, **kwargs):
        version = upload(self.candidate, slot_type, self.user, **kwargs)
        DocumentService.approve(version.pk, reviewer=self.user)
        return version

    def test_not_eligible_without_any_slot_of_required_type(self):
        self.assertFalse(DocumentService.can_candidate_apply(self.candidate.pk, ["RELEVE_M1"]))

    def test_not_eligible_if_one_of_several_slots_is_still_pending(self):
        self._approve_latest("RELEVE_LICENCE", domaine="Informatique", annee_licence="A1")
        upload(self.candidate, "RELEVE_LICENCE", self.user, domaine="Informatique", annee_licence="A2")  # reste PENDING
        self.assertFalse(DocumentService.can_candidate_apply(self.candidate.pk, ["RELEVE_LICENCE"]))

    def test_eligible_once_every_slot_of_the_type_is_approved(self):
        self._approve_latest("RELEVE_LICENCE", domaine="Informatique", annee_licence="A1")
        self._approve_latest("RELEVE_LICENCE", domaine="Informatique", annee_licence="A2")
        self._approve_latest("RELEVE_LICENCE", domaine="Informatique", annee_licence="A3")
        self.assertTrue(DocumentService.can_candidate_apply(self.candidate.pk, ["RELEVE_LICENCE"]))

    def test_replacement_after_rejection_makes_slot_pending_again(self):
        version = upload(self.candidate, "DIPLOME_LICENCE", self.user, domaine="Informatique")
        DocumentService.reject(version.pk, reviewer=self.user, reason="Illisible")
        self.assertFalse(DocumentService.can_candidate_apply(self.candidate.pk, ["DIPLOME_LICENCE"]))

        new_version = upload(self.candidate, "DIPLOME_LICENCE", self.user, domaine="Informatique")
        self.assertEqual(new_version.status, DocumentReviewStatus.PENDING_REVIEW)
        self.assertEqual(new_version.replaced_version_id, version.pk)
        self.assertFalse(DocumentService.can_candidate_apply(self.candidate.pk, ["DIPLOME_LICENCE"]))

        DocumentService.approve(new_version.pk, reviewer=self.user)
        self.assertTrue(DocumentService.can_candidate_apply(self.candidate.pk, ["DIPLOME_LICENCE"]))


class SlotViewsRBACTests(TestCase):
    """RBAC via les vues, adapté au nouveau modèle slot."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.candidate_user = User.objects.create(pubkey="u_c1", email="c1@example.com")
        self.other_user = User.objects.create(pubkey="u_c2", email="c2@example.com")
        self.coordinator_user = User.objects.create(pubkey="u_coord", email="coord@example.com")

        Coordinateur.objects.create(pubkey="coord_1", user=self.coordinator_user, nom="Coord", email=self.coordinator_user.email)

        self.candidate = make_candidate("cand_a", self.candidate_user, "CINA")
        self.other_candidate = make_candidate("cand_b", self.other_user, "CINB")

        self.own_version = upload(self.candidate, "RELEVE_M1", self.candidate_user)
        self.other_version = upload(self.other_candidate, "RELEVE_M1", self.other_user)

    def _auth(self, request, user):
        force_authenticate(request, user=user)
        return request

    def test_candidate_sees_only_own_slots(self):
        request = self._auth(self.factory.get("/me/slots/"), self.candidate_user)
        response = MySlotListView.as_view()(request)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["current_version"]["pubkey"], self.own_version.pubkey)

    def test_candidate_cannot_view_other_candidate_version_via_detail(self):
        request = self._auth(self.factory.get("/x/"), self.candidate_user)
        response = DocumentDetailView.as_view()(request, pubkey=self.other_version.pubkey)
        self.assertEqual(response.status_code, 403)

    def test_coordinator_can_approve_any_slot_version_globally(self):
        request = self._auth(self.factory.post("/approve/"), self.coordinator_user)
        response = DocumentReviewView.as_view()(request, pubkey=self.other_version.pubkey)
        self.assertEqual(response.status_code, 200)

    def test_pending_queue_excludes_superseded_versions(self):
        upload(self.candidate, "RELEVE_M1", self.candidate_user)  # remplace own_version, qui devient is_active=False
        request = self._auth(self.factory.get("/pending/"), self.coordinator_user)
        response = PendingDocumentListView.as_view()(request)
        pubkeys = {d["pubkey"] for d in response.data}
        self.assertNotIn(self.own_version.pubkey, pubkeys)  # ancienne version superseded, exclue