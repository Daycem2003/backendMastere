from django.db import models

from src.shared.models import ManagedModel


class RolePermission(ManagedModel):
    role = models.ForeignKey("authorization.Role", on_delete=models.CASCADE, related_name="role_permissions", db_column="roleId")
    permission = models.ForeignKey("authorization.Permission", on_delete=models.CASCADE, related_name="role_permissions", db_column="permissionId")
    created_at = models.DateTimeField(null=True, blank=True, db_column="createdAt", db_default=models.functions.Now())

    class Meta:
        db_table = "AUTH_ROLE_PERMISSIONS"
        constraints = [models.UniqueConstraint(fields=["role", "permission"], name="auth_role_permission_unique")]
