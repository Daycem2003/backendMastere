from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from src.apps.administrator.models import Administrateur
from src.apps.candidate_profile.models import CandidateProfile
from src.apps.candidate_profile.views.candidate_profile_views import (
    CandidateProfileDetailView,
    CandidateProfileListView,
)
from src.apps.coordinator.models import Coordinateur

User = get_user_model()


class CandidateProfileAPITests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.coord_user = User.objects.create(pubkey="user_coord", email="coord@example.com")
        Coordinateur.objects.create(
            pubkey="coord_profile", user=self.coord_user, nom="Coord", email=self.coord_user.email
        )

        self.cand_user = User.objects.create(pubkey="user_cand", email="cand@example.com")

        self.profile1 = CandidateProfile.objects.create(
            pubkey="cand_001",
            nom="Ben Ali",
            prenom="Sami",
            cin="08888888",
            email="sami@example.com",
            telephone="20111222",
            ville="Tunis",
            nationalite="Tunisienne",
            annee_naissance=2000,
            statut="EN_ATTENTE",
        )

        self.profile2 = CandidateProfile.objects.create(
            pubkey="cand_002",
            nom="Trabelsi",
            prenom="Amina",
            cin="09999999",
            email="amina@example.com",
            telephone="20333444",
            ville="Sousse",
            nationalite="Tunisienne",
            annee_naissance=2001,
            statut="VALIDE",
        )

    def test_list_requires_coordinator_or_admin(self):
        # Unauthenticated -> 401 or 403
        request = self.factory.get("/api/v1/candidates/")
        response = CandidateProfileListView.as_view()(request)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Candidate user -> 403
        request = self.factory.get("/api/v1/candidates/")
        force_authenticate(request, user=self.cand_user)
        response = CandidateProfileListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Coordinator -> 200
        request = self.factory.get("/api/v1/candidates/")
        force_authenticate(request, user=self.coord_user)
        response = CandidateProfileListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_filter_by_status(self):
        request = self.factory.get("/api/v1/candidates/", {"statut": "EN_ATTENTE"})
        force_authenticate(request, user=self.coord_user)
        response = CandidateProfileListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pubkey"], "cand_001")

    def test_list_filter_by_search_query(self):
        request = self.factory.get("/api/v1/candidates/", {"q": "amina"})
        force_authenticate(request, user=self.coord_user)
        response = CandidateProfileListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pubkey"], "cand_002")

    def test_detail_view_coordinator(self):
        request = self.factory.get(f"/api/v1/candidates/{self.profile1.pubkey}")
        force_authenticate(request, user=self.coord_user)
        response = CandidateProfileDetailView.as_view()(request, pubkey=self.profile1.pubkey)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pubkey"], "cand_001")
        self.assertEqual(response.data["nom"], "Ben Ali")
