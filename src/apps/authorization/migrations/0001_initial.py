from django.db import migrations, models
import django.db.models.deletion
from django.db.models.functions import Now


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("code", models.TextField(unique=True)),
                ("resource", models.TextField()),
                ("action", models.TextField()),
                ("description", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(blank=True, db_column="createdAt", db_default=Now(), null=True)),
                ("updated_at", models.DateTimeField(blank=True, db_column="updatedAt", null=True)),
            ],
            options={"db_table": "AUTH_PERMISSIONS"},
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("code", models.TextField(unique=True)),
                ("name", models.TextField()),
                ("description", models.TextField(blank=True, null=True)),
                ("is_system", models.BooleanField(db_column="isSystem", default=False)),
                ("created_at", models.DateTimeField(blank=True, db_column="createdAt", db_default=Now(), null=True)),
                ("updated_at", models.DateTimeField(blank=True, db_column="updatedAt", null=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
            ],
            options={"db_table": "AUTH_ROLES"},
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(blank=True, db_column="createdAt", db_default=Now(), null=True)),
                ("permission", models.ForeignKey(db_column="permissionId", on_delete=django.db.models.deletion.CASCADE, related_name="role_permissions", to="authorization.permission")),
                ("role", models.ForeignKey(db_column="roleId", on_delete=django.db.models.deletion.CASCADE, related_name="role_permissions", to="authorization.role")),
            ],
            options={"db_table": "AUTH_ROLE_PERMISSIONS", "constraints": [models.UniqueConstraint(fields=("role", "permission"), name="auth_role_permission_unique")]},
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("assigned_at", models.DateTimeField(blank=True, db_column="assignedAt", db_default=Now(), null=True)),
                ("assigned_by", models.ForeignKey(blank=True, db_column="assignedById", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_roles", to="users.user")),
                ("role", models.ForeignKey(db_column="roleId", on_delete=django.db.models.deletion.CASCADE, related_name="user_assignments", to="authorization.role")),
                ("user", models.ForeignKey(db_column="userId", on_delete=django.db.models.deletion.CASCADE, related_name="role_assignments", to="users.user")),
            ],
            options={"db_table": "AUTH_USER_ROLES", "constraints": [models.UniqueConstraint(fields=("user", "role"), name="auth_user_role_unique")]},
        ),
    ]
