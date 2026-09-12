from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.masters.exceptions.master_exceptions import MasterNotFound
from src.apps.administrator.models import Administrateur
from src.apps.masters.permissions.master_permissions import CanPublishMaster
from src.apps.masters.selectors.master_selector import get_by_pubkey
from src.apps.masters.serializers.master import MasterSerializer


class AssignAdministrateurView(APIView):
    """Rattache un master à l'administrateur courant (supervision), en plus
    de son coordinateur. Réservé aux admins (même contrainte que la
    publication)."""

    permission_classes = [CanPublishMaster]

    def post(self, request, pubkey):
        master = get_by_pubkey(pubkey)
        if not master:
            raise MasterNotFound()

        administrateur = getattr(request.user, "administrateur", None)
        if administrateur is None:
            return Response({"detail": "Aucun profil administrateur pour cet utilisateur."}, status=403)

        master.administrateur = administrateur
        master.save(update_fields=["administrateur"])
        return Response(MasterSerializer(master).data)
