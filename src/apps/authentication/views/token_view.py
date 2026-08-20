from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.dto.refresh_token import RefreshTokenRequestDTO
from src.apps.authentication.guards.jwt_refresh_token_guard import JwtRefreshTokenGuard
from src.apps.authentication.dto.update_profile import UpdateProfileRequestDTO
from src.apps.authentication.services.authentication_service import AuthenticationService
from src.apps.authentication.services.token_service import TokenService

from . import auth_response, validate_dto


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = validate_dto(RefreshTokenRequestDTO, request.data)
        JwtRefreshTokenGuard.validate(payload.refresh_token)
        tokens = TokenService.refresh_access_token(payload.refresh_token)
        return Response({"access_token": tokens.access_token, "refresh_token": tokens.refresh_token})


class MeView(APIView):
    def get(self, request):
        return Response(auth_response(request.user)["user"])

    def patch(self, request):
        payload = validate_dto(UpdateProfileRequestDTO, request.data)
        AuthenticationService.update_profile(request.user.pubkey, payload)
        request.user.refresh_from_db()
        return Response(auth_response(request.user)["user"])
