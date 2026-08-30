from django.db import migrations, models

import src.shared.models


class Migration(migrations.Migration):
    initial = True

    dependencies = ()

    operations = (
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'UserRoleEnum') THEN
                    CREATE TYPE "UserRoleEnum" AS ENUM ('CANDIDATE', 'COORDINATOR', 'ADMIN');
                END IF;
            END
            $$;
            """,
            reverse_sql="""
            -- No destructive drop of enum
            """,
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("email", models.TextField(unique=True)),
                ("password", models.TextField()),
                (
                    "role",
                    src.shared.models.PostgreSQLEnumField(
                        choices=[
                            ("CANDIDATE", "Candidate"),
                            ("COORDINATOR", "Coordinator"),
                            ("ADMIN", "Administrator"),
                        ],
                        default="CANDIDATE",
                        enum_name="UserRoleEnum",
                        max_length=255,
                    ),
                ),
                ("is_active", models.BooleanField(db_column="isActive", default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt", null=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
            ],
            options={
                "db_table": "MST_USERS",
            },
        ),
    )
