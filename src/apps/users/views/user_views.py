from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.users.dto.user import SetActiveStatusDTO
from src.apps.users.exceptions.user_exceptions import UserAccessForbidden, UserNotFound
from src.apps.users.permissions.user_permissions import IsAdmin
from src.apps.users.policies.user_policy import UserPolicy
from src.apps.users.selectors.user_selector import get_by_pubkey, list_all, list_by_rbac_role_code
from src.apps.users.serializers.user import SetActiveStatusSerializer, UserSerializer
from src.apps.users.services.user_service import UserService


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # request.user n'est pas annoté par un selector (vient du middleware
        # d'auth) -> on repasse par get_by_pubkey pour obtenir rbac_role_code.
        user = get_by_pubkey(request.user.pubkey)
        return Response(UserSerializer(user).data)


class UserListView(APIView):
    """L'assignation de rôle ne vit plus ici — voir `authorization_patch`
    pour `POST /authorization/users/<pubkey>/role`."""

    permission_classes = [IsAdmin]

    def get(self, request):
        role_code = request.query_params.get("role")
        is_active_param = request.query_params.get("is_active")
        is_active = None
        if is_active_param is not None:
            is_active = is_active_param.lower() == "true"

        users = list_by_rbac_role_code(role_code) if role_code else list_all(is_active=is_active)
        return Response(UserSerializer(users, many=True).data)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pubkey):
        target = get_by_pubkey(pubkey)
        if not target:
            raise UserNotFound()
        if not UserPolicy.can_view(request.user, target):
            raise UserAccessForbidden()
        return Response(UserSerializer(target).data)


class SetUserActiveStatusView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pubkey):
        target = get_by_pubkey(pubkey)
        if not target:
            raise UserNotFound()
        if not UserPolicy.can_deactivate(request.user, target):
            raise UserAccessForbidden()

        serializer = SetActiveStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = SetActiveStatusDTO(**serializer.validated_data)
        target = UserService.set_active_status(target, dto, actor=request.user)
        return Response(UserSerializer(target).data)
