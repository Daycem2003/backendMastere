from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.activate_account import ActivateAccountRequestDTO
from src.apps.authentication.services.account_activation_service import (
    AccountActivationService,
)

from . import validate_dto


class ActivateAccountView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        dto = validate_dto(ActivateAccountRequestDTO, request.data)
        AccountActivationService.activate_account(dto.token, dto.password)
        return Response(
            {"message": "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter."},
            status=status.HTTP_200_OK,
        )
