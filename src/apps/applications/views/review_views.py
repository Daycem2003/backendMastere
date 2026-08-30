from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.applications.permissions.application_permissions import CanReviewApplications
from src.apps.applications.selectors.application_selector import list_for_master
from src.apps.applications.serializers.application import ApplicationSerializer


class MasterApplicationListView(APIView):
    """Liste des candidatures pour un master donné, triées par score
    décroissant puis date de soumission — vue de travail du coordinateur."""

    permission_classes = [CanReviewApplications]

    def get(self, request, master_pubkey):
        statut = request.query_params.get("statut")
        applications = list_for_master(master_pubkey, statut=statut)
        return Response(ApplicationSerializer(applications, many=True).data)
