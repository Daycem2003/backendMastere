from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.forgot_password import ForgotPasswordRequestDTO
from src.apps.authentication.dto.reset_password import ResetPasswordRequestDTO
from src.apps.authentication.services.password_service import PasswordService

from . import validate_dto


class PasswordForgotView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        PasswordService.request_reset(validate_dto(ForgotPasswordRequestDTO, request.data))
        return Response({"message": "Si le compte existe, un lien de réinitialisation a été envoyé."})


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        PasswordService.reset_password(validate_dto(ResetPasswordRequestDTO, request.data))
        return Response({"message": "Mot de passe réinitialisé."})
