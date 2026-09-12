from datetime import datetime, timedelta, timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from src.apps.coordinator.models import Coordinateur
from src.apps.masters.models import Master, MasterStatus
from src.apps.masters.views.master_views import MasterDetailView

User = get_user_model()


class MasterAPITests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.coord_user = User.objects.create(pubkey="usr_coord_1", email="coord1@example.com")
        self.coord = Coordinateur.objects.create(
            pubkey="coord_1", user=self.coord_user, nom="Coordinateur Test", email=self.coord_user.email
        )

        self.other_user = User.objects.create(pubkey="usr_other_1", email="other@example.com")

        now = datetime.now(timezone.utc)
        self.master = Master.objects.create(
            pubkey="mst_test_01",
            nom="Master Génie Logiciel",
            universite="Université de Tunis",
            ville="Tunis",
            domaine="Informatique",
            discipline="Génie Logiciel",
            specialite="Ingénierie des Systèmes",
            nombre_places=30,
            date_debut=now,
            date_fin=now + timedelta(days=30),
            statut=MasterStatus.BROUILLON,
            coordinateur=self.coord,
        )

    def test_coordinator_can_view_own_master_draft_with_all_fields(self):
        request = self.factory.get(f"/api/v1/masters/{self.master.pubkey}")
        force_authenticate(request, user=self.coord_user)
        response = MasterDetailView.as_view()(request, pubkey=self.master.pubkey)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pubkey"], "mst_test_01")
        self.assertEqual(response.data["nom"], "Master Génie Logiciel")
        self.assertEqual(response.data["domaine"], "Informatique")
        self.assertEqual(response.data["discipline"], "Génie Logiciel")
        self.assertEqual(response.data["specialite"], "Ingénierie des Systèmes")
        self.assertEqual(response.data["nombre_places"], 30)
        self.assertEqual(response.data["statut"], "BROUILLON")
        self.assertEqual(response.data["coordinateur_pubkey"], "coord_1")
        self.assertIn("date_debut", response.data)
        self.assertIn("date_fin", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertIn("type_licences_acceptees", response.data)
        self.assertIn("required_documents", response.data)

    def test_other_unauthorized_user_cannot_view_draft_master(self):
        request = self.factory.get(f"/api/v1/masters/{self.master.pubkey}")
        force_authenticate(request, user=self.other_user)
        response = MasterDetailView.as_view()(request, pubkey=self.master.pubkey)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
