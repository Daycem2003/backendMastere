"""Migration state-only — MST_APPLICATIONS est une table legacy du schéma
Prisma de référence (managed=False). Aucun DDL exécuté ici."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("candidate_profile", "__first__"),
        ("masters", "__first__"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Application",
                    fields=[
                        ("id", models.AutoField(primary_key=True, serialize=False)),
                        ("pubkey", models.TextField(unique=True)),
                        ("niveau", models.TextField()),
                        ("date_soumission", models.DateTimeField(auto_now_add=True, db_column="dateSoumission")),
                        ("score", models.FloatField(blank=True, null=True)),
                        ("statut", models.CharField(choices=[("SOUMISE", "Soumise"), ("EN_COURS", "En cours"), ("ACCEPTEE", "Acceptée"), ("REJETEE", "Rejetée")], default="SOUMISE", max_length=16)),
                        ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                        ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                        ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                        ("candidate_profile", models.ForeignKey(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="candidate_profile.candidateprofile")),
                        ("master", models.ForeignKey(db_column="masterId", on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="masters.master")),
                    ],
                    options={
                        "db_table": "MST_APPLICATIONS",
                        "managed": False,
                        "indexes": [
                            models.Index(fields=["candidate_profile", "statut"], name="app_cand_statut_idx"),
                            models.Index(fields=["master", "statut"], name="app_master_statut_idx"),
                        ],
                        "constraints": [
                            models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("candidate_profile", "master"), name="applications_one_active_per_master"),
                        ],
                    },
                ),
            ],
        ),
    ]
