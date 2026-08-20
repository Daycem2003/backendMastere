from django.db import models

from src.shared.models import ManagedModel


class UserRole(ManagedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="role_assignments", db_column="userId")
    role = models.ForeignKey("authorization.Role", on_delete=models.CASCADE, related_name="user_assignments", db_column="roleId")
    assigned_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles", db_column="assignedById")
    assigned_at = models.DateTimeField(null=True, blank=True, db_column="assignedAt", db_default=models.functions.Now())

    class Meta:
        db_table = "AUTH_USER_ROLES"
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="auth_user_role_unique")]
