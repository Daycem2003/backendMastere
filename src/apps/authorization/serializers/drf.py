from django.core.validators import RegexValidator
from rest_framework import serializers

from src.apps.authorization.models import Permission, Role


class RoleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("code", "name", "description")
        extra_kwargs = {
            "code": {"validators": [RegexValidator(r"^[A-Z_]+$")]},
        }


class RoleResponseSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ("pubkey", "code", "name", "description", "is_system", "permissions")
        read_only_fields = fields

    def get_permissions(self, role):
        return [
            {
                "code": link.permission.code,
                "resource": link.permission.resource,
                "action": link.permission.action,
            }
            for link in role.role_permissions.select_related("permission").all()
        ]


class PermissionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("pubkey", "code", "resource", "action", "description")
        read_only_fields = fields


class RoleAssignmentSerializer(serializers.Serializer):
    user_pubkey = serializers.CharField(max_length=255)
    role_code = serializers.CharField(max_length=255)
