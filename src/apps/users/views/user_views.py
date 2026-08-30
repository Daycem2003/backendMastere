from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.users.dto.user import (
    ChangePasswordDTO,
    UpdateUserDTO,
    UserFilterDTO,
)
from src.apps.users.exceptions.user_exceptions import (
    UserAccessDeniedException,
    UserNotFoundException,
)
from src.apps.users.permissions.user_permissions import (
    CanListUsersPermission,
    CanManageUserLifecyclePermission,
)
from src.apps.users.policies.user_policy import UserPolicy
from src.apps.users.selectors.user_selector import (
    count_users,
    get_user_by_pubkey,
    list_users,
)
from src.apps.users.serializers.user import (
    ChangePasswordSerializer,
    UpdateUserSerializer,
    UserActionReasonSerializer,
    UserSerializer,
)
from src.apps.users.services.user_lifecycle_service import UserLifecycleService
from src.apps.users.services.user_service import UserService


class CurrentUserView(APIView):
    """Endpoints for current authenticated user profile."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateUserSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = UpdateUserDTO(**serializer.validated_data)
        updated_user = UserService.update_user(request.user, dto)
        return Response(UserSerializer(updated_user).data)


class ChangePasswordView(APIView):
    """Endpoint to change the current authenticated user's password."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = ChangePasswordDTO(**serializer.validated_data)
        UserService.change_password(request.user, dto)
        return Response(
            {"message": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK,
        )


class UserListView(APIView):
    """Endpoint to list users (accessible to ADMIN and COORDINATOR)."""

    permission_classes = (permissions.IsAuthenticated, CanListUsersPermission)

    def get(self, request):
        search = request.query_params.get("search")
        is_active_raw = request.query_params.get("is_active")
        is_deleted_raw = request.query_params.get("is_deleted")

        is_active = None
        if is_active_raw is not None:
            is_active = is_active_raw.lower() in ("true", "1", "t")

        is_deleted = None
        if is_deleted_raw is not None:
            is_deleted = is_deleted_raw.lower() in ("true", "1", "t")

        try:
            limit = int(request.query_params.get("limit", 50))
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            limit, offset = 50, 0

        filters = UserFilterDTO(
            search=search,
            is_active=is_active,
            is_deleted=is_deleted,
            limit=limit,
            offset=offset,
        )

        total = count_users(filters)
        users = list_users(filters)[offset : offset + limit]

        return Response(
            {
                "count": total,
                "limit": limit,
                "offset": offset,
                "results": UserSerializer(users, many=True).data,
            }
        )


class UserDetailView(APIView):
    """Endpoint to retrieve or update a specific user."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pubkey: str):
        target_user = get_user_by_pubkey(pubkey, include_deleted=True)
        if not target_user:
            raise UserNotFoundException()

        if not UserPolicy.can_view_user(request.user, target_user):
            raise UserAccessDeniedException()

        return Response(UserSerializer(target_user).data)

    def patch(self, request, pubkey: str):
        target_user = get_user_by_pubkey(pubkey, include_deleted=True)
        if not target_user:
            raise UserNotFoundException()

        if not UserPolicy.can_update_user(request.user, target_user):
            raise UserAccessDeniedException()

        serializer = UpdateUserSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        dto = UpdateUserDTO(**serializer.validated_data)
        updated_user = UserService.update_user(target_user, dto)
        return Response(UserSerializer(updated_user).data)

    def delete(self, request, pubkey: str):
        target_user = get_user_by_pubkey(pubkey, include_deleted=True)
        if not target_user:
            raise UserNotFoundException()

        if not UserPolicy.can_manage_user_lifecycle(request.user, target_user):
            raise UserAccessDeniedException()

        user = UserLifecycleService.soft_delete_user(pubkey, actor=request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)



class UserActivateView(APIView):
    """Endpoint to activate a user account."""

    permission_classes = (permissions.IsAuthenticated, CanManageUserLifecyclePermission)

    def post(self, request, pubkey: str):
        user = UserLifecycleService.activate_user(pubkey, actor=request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class UserDeactivateView(APIView):
    """Endpoint to deactivate a user account."""

    permission_classes = (permissions.IsAuthenticated, CanManageUserLifecyclePermission)

    def post(self, request, pubkey: str):
        serializer = UserActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason")
        user = UserLifecycleService.deactivate_user(
            pubkey, actor=request.user, reason=reason
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class UserSoftDeleteView(APIView):
    """Endpoint to soft-delete a user account."""

    permission_classes = (permissions.IsAuthenticated, CanManageUserLifecyclePermission)

    def post(self, request, pubkey: str):
        serializer = UserActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason")
        user = UserLifecycleService.soft_delete_user(
            pubkey, actor=request.user, reason=reason
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request, pubkey: str):
        user = UserLifecycleService.soft_delete_user(pubkey, actor=request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class UserRestoreView(APIView):
    """Endpoint to restore a soft-deleted user account."""

    permission_classes = (permissions.IsAuthenticated, CanManageUserLifecyclePermission)

    def post(self, request, pubkey: str):
        user = UserLifecycleService.restore_user(pubkey, actor=request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
