from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authorization.permissions.drf import require_permission
from .services.permission_service import PermissionService
from .services.role_service import RoleService


class PermissionListView(APIView):
    permission_classes = [require_permission("permission:manage")]

    def get(self, request):
        permissions = async_to_sync(PermissionService.list_permissions)()
        return Response([{"pubkey": p.pubkey, "code": p.code, "resource": p.resource, "action": p.action, "description": p.description} for p in permissions])


class RoleListView(APIView):
    permission_classes = [require_permission("role:manage")]

    def get(self, request):
        roles = async_to_sync(RoleService.list_roles)()
        return Response([{"pubkey": role.pubkey, "code": role.code, "name": role.name, "description": role.description, "is_system": role.is_system} for role in roles])

    def post(self, request):
        role = async_to_sync(RoleService.create_custom_role)(request.data["code"], request.data["name"], request.data.get("description"))
        return Response({"pubkey": role.pubkey, "code": role.code, "name": role.name}, status=status.HTTP_201_CREATED)
