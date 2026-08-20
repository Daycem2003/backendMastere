from asgiref.sync import async_to_sync
from rest_framework import generics, permissions, status
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
from src.apps.authorization.services.role_assignment_service import RoleAssignmentService
from src.apps.authorization.services.role_service import RoleService


class PermissionListView(APIView):
    permission_classes = [require_permission("permission:manage")]

    def get(self, request):
        permissions = async_to_sync(PermissionService.list_permissions)()
        return Response(PermissionResponseSerializer(permissions, many=True).data)


class RoleListCreateView(APIView):
    permission_classes = [require_permission("role:manage")]

    def get(self, request):
        roles = async_to_sync(RoleService.list_roles)()
        return Response(RoleResponseSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RoleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = async_to_sync(RoleService.create_custom_role)(**serializer.validated_data)
        return Response(RoleResponseSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [require_permission("role:manage")]

    def get(self, request, pubkey):
        role = async_to_sync(RoleService.get_role)(pubkey)
        return Response(RoleResponseSerializer(role).data)

    def patch(self, request, pubkey):
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

    def delete(self, request, pubkey):
        async_to_sync(RoleService.delete_role)(pubkey)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleAssignmentCreateView(APIView):
    permission_classes = [require_permission("user_role:assign")]

    def post(self, request):
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = RoleAssignmentService.assign_role(
            user_pubkey=serializer.validated_data["user_pubkey"],
            role_code=serializer.validated_data["role_code"],
            assigned_by_pubkey=request.user.pubkey,
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
    permission_classes = [require_permission("user_role:assign")]

    def delete(self, request, user_pubkey, role_code):
        RoleAssignmentService.revoke_role(user_pubkey, role_code)
        return Response(status=status.HTTP_204_NO_CONTENT)
