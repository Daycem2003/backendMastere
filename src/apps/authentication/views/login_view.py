from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.id_number_authentication import IdNumberAuthRequestDTO
from src.apps.authentication.dto.login import LoginRequestDTO
from src.apps.authentication.dto.phone_authentication import PhoneAuthRequestDTO
from src.apps.authentication.services.authentication_service import AuthenticationService
from src.apps.authentication.services.otp_service import OtpService

from . import auth_response, validate_dto


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = AuthenticationService.login(validate_dto(LoginRequestDTO, request.data))
        return Response(auth_response(user))


class IdNumberLoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = validate_dto(IdNumberAuthRequestDTO, request.data)
        AuthenticationService.initiate_id_number_login(payload)
        OtpService.send_otp(payload.telephone)
        return Response({"message": "Code envoyé."}, status=status.HTTP_200_OK)


class PhoneLoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = validate_dto(PhoneAuthRequestDTO, request.data)
        AuthenticationService.initiate_phone_login(payload)
        OtpService.send_otp(payload.telephone)
        return Response({"message": "Code envoyé."}, status=status.HTTP_200_OK)
