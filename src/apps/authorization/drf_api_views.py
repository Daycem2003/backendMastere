from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authorization.permissions.drf import require_permission
from src.apps.authorization.serializers.drf import (
    PermissionResponseSerializer,
    RoleAssignmentSerializer,
    RoleResponseSerializer,
    RoleWriteSerializer,
)
from src.apps.authorization.services.permission_service import PermissionService
from src.apps.authorization.services.role_assignment_service import (
    RoleAssignmentService,
)
from src.apps.authorization.services.role_service import RoleService


class PermissionListView(APIView):
    """List all available RBAC permissions in the system."""

    permission_classes = (require_permission("permission:manage"),)

    def get(self, request):
        permissions_list = async_to_sync(PermissionService.list_permissions)()
        return Response(PermissionResponseSerializer(permissions_list, many=True).data)


class RoleListCreateView(APIView):
    """List all roles or create a new custom role."""

    permission_classes = (require_permission("role:manage"),)

    def get(self, request):
        roles = async_to_sync(RoleService.list_roles)()
        return Response(RoleResponseSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RoleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = async_to_sync(RoleService.create_custom_role)(**serializer.validated_data)
        return Response(RoleResponseSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    """Retrieve, update, or delete a specific role."""

    permission_classes = (require_permission("role:manage"),)

    def get(self, request, pubkey: str):
        role = async_to_sync(RoleService.get_role)(pubkey)
        return Response(RoleResponseSerializer(role).data)

    def patch(self, request, pubkey: str):
        serializer = RoleWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        current_role = async_to_sync(RoleService.get_role)(pubkey)
        role = async_to_sync(RoleService.update_role)(
            pubkey,
            name=serializer.validated_data.get("name", current_role.name),
            description=serializer.validated_data.get(
                "description", current_role.description
            ),
        )
        return Response(RoleResponseSerializer(role).data)

    def delete(self, request, pubkey: str):
        async_to_sync(RoleService.delete_role)(pubkey)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionManagementView(APIView):
    """Assign or revoke a permission on a role."""

    permission_classes = (require_permission("role:manage"),)

    def post(self, request, pubkey: str, permission_code: str):
        role = async_to_sync(RoleService.assign_permission_to_role)(
            pubkey, permission_code
        )
        return Response(RoleResponseSerializer(role).data, status=status.HTTP_200_OK)

    def delete(self, request, pubkey: str, permission_code: str):
        role = async_to_sync(RoleService.revoke_permission_from_role)(
            pubkey, permission_code
        )
        return Response(RoleResponseSerializer(role).data, status=status.HTTP_200_OK)


class RoleAssignmentCreateView(APIView):
    """Assign a role to a user."""

    permission_classes = (require_permission("user_role:assign"),)

    def post(self, request):
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = RoleAssignmentService.assign_role(
            user_pubkey=serializer.validated_data["user_pubkey"],
            role_code=serializer.validated_data["role_code"],
            assigned_by_pubkey=request.user.pubkey if request.user else None,
        )
        return Response(
            {
                "user_pubkey": serializer.validated_data["user_pubkey"],
                "role_code": assignment.role.code,
                "assigned_at": assignment.assigned_at,
            },
            status=status.HTTP_201_CREATED,
        )


class RoleAssignmentDeleteView(APIView):
    """Revoke a role from a user."""

    permission_classes = (require_permission("user_role:assign"),)

    def delete(self, request, user_pubkey: str, role_code: str):
        RoleAssignmentService.revoke_role(user_pubkey, role_code)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoleListView(APIView):
    """List all RBAC roles assigned to a user."""

    permission_classes = (require_permission("user_role:assign"),)

    def get(self, request, user_pubkey: str):
        user_roles = RoleAssignmentService.list_user_roles(user_pubkey)
        roles = [ur.role for ur in user_roles]
        return Response(RoleResponseSerializer(roles, many=True).data, status=status.HTTP_200_OK)
