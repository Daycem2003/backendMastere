"""Migration state-only.

MST_NOTIFICATION_RECORDS est une table du schéma Prisma de référence
(managed=False côté Django, comme MST_DOCUMENTS). Cette migration
n'exécute donc AUCUN DDL en base — elle enregistre uniquement l'état du
modèle pour Django (nécessaire à makemigrations/migrate pour les FKs
d'autres apps qui pointeraient vers ce modèle).

La modification réelle du schéma (ajout de `candidateProfileId`, passage
de `applicationId` en optionnel, ajout de `luLe`) doit être appliquée côté
base de données via `prisma migrate dev` en utilisant
`_PRISMA_SCHEMA_PATCH.prisma` fourni à la racine du zip.
"""
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
                    name="NotificationRecord",
                    fields=[
                        ("id", models.AutoField(primary_key=True, serialize=False)),
                        ("pubkey", models.TextField(unique=True)),
                        ("motif", models.CharField(max_length=32, choices=[
                            ("DOCUMENT_MANQUANT", "Document manquant"),
                            ("DOCUMENT_FRAUDULEUX", "Document frauduleux"),
                            ("DOCUMENT_REJETE", "Document rejeté"),
                            ("CANDIDATURE_STATUT", "Changement de statut de candidature"),
                            ("AUTRE", "Autre"),
                        ])),
                        ("document_concerne", models.TextField(blank=True, db_column="documentConcerne", null=True)),
                        ("objet", models.TextField()),
                        ("corps", models.TextField()),
                        ("lu_le", models.DateTimeField(blank=True, db_column="luLe", null=True)),
                        ("envoyee_le", models.DateTimeField(auto_now_add=True, db_column="envoyeeLe")),
                        ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                        ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                        ("candidate_profile", models.ForeignKey(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="candidate_profile.candidateprofile")),
                        ("application", models.ForeignKey(blank=True, db_column="applicationId", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="masters.application")),
                    ],
                    options={
                        "db_table": "MST_NOTIFICATION_RECORDS",
                        "managed": False,
                        "indexes": [
                            models.Index(fields=["candidate_profile", "lu_le"], name="notif_cand_lu_idx"),
                            models.Index(fields=["application"], name="notif_application_idx"),
                        ],
                    },
                ),
            ],
        ),
    ]
