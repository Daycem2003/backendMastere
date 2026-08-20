from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.otp_verify import OtpVerifyRequestDTO
from src.apps.authentication.services.authentication_service import AuthenticationService
from src.apps.authentication.services.otp_service import OtpService

from . import auth_response, validate_dto


class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = validate_dto(OtpVerifyRequestDTO, request.data)
        OtpService.verify_otp(payload)
        user = AuthenticationService.complete_otp_login(payload.telephone)
        return Response(auth_response(user))
