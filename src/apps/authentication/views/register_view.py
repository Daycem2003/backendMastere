from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.register import RegisterRequestDTO
from src.apps.authentication.services.authentication_service import AuthenticationService

from . import auth_response, validate_dto


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = validate_dto(RegisterRequestDTO, request.data)
        user = AuthenticationService.register(payload)
        return Response(auth_response(user), status=status.HTTP_201_CREATED)
