from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("authorization", "0001_initial"),
        ("candidate_profile", "__first__"),
        ("users", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentVersion",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("version_number", models.PositiveIntegerField(db_column="versionNumber")),
                ("document_type", models.CharField(db_column="documentType", max_length=32)),
                ("status", models.CharField(choices=[("PENDING_REVIEW", "Pending review"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING_REVIEW", max_length=20)),
                ("storage_key", models.TextField(db_column="storageKey")),
                ("mime_type", models.CharField(db_column="mimeType", max_length=255)),
                ("file_size", models.PositiveBigIntegerField(db_column="fileSize")),
                ("checksum", models.CharField(blank=True, default="", max_length=128)),
                ("is_active", models.BooleanField(db_column="isActive", default=True)),
                ("reviewed_at", models.DateTimeField(blank=True, db_column="reviewedAt", null=True)),
                ("rejection_reason", models.TextField(blank=True, db_column="rejectionReason", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("reviewer", models.ForeignKey(blank=True, db_column="reviewerId", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_document_versions", to="users.user")),
                ("candidate_profile", models.ForeignKey(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="document_versions", to="candidate_profile.candidateprofile")),
                ("document", models.ForeignKey(blank=True, db_column="documentId", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="documents.document")),
                ("replaced_version", models.ForeignKey(blank=True, db_column="replacedVersionId", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="replacements", to="documents.documentversion")),
            ],
            options={"db_table": "DOCUMENT_VERSIONS", "constraints": [models.UniqueConstraint(fields=("document", "version_number"), name="documents_document_version_unique")], "indexes": [models.Index(fields=["candidate_profile", "status"], name="documents_cand_status_idx"), models.Index(fields=["candidate_profile", "is_active"], name="documents_cand_active_idx")]},
        ),
        migrations.CreateModel(
            name="DocumentAuditEvent",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("action", models.CharField(max_length=32)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("actor", models.ForeignKey(db_column="actorId", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="document_audit_events", to="users.user")),
                ("document_version", models.ForeignKey(db_column="documentVersionId", on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="documents.documentversion")),
            ],
            options={"db_table": "DOCUMENT_AUDIT_EVENTS", "indexes": [models.Index(fields=["document_version", "created_at"], name="documents_audit_idx")]},
        ),
    ]
