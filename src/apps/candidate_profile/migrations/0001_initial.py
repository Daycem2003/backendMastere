"""Migration state-only — toutes les tables de ce module sont des tables
legacy du schéma Prisma de référence (managed=False), comme MST_DOCUMENTS
dans le module `documents`. Aucun DDL n'est exécuté ici ; la modification
réelle (ajout de `Master1Year.masterId`, cf. modèle) doit être appliquée
côté base via `prisma migrate dev` avec `_PRISMA_SCHEMA_PATCH.prisma`.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("users", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="TypeLicence",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("intitule", models.TextField()),
                ("domaine", models.TextField()),
                ("est_eligible", models.BooleanField(db_column="estEligible", default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
            ],
            options={"db_table": "MST_TYPE_LICENCES"},
        ),
        migrations.CreateModel(
            name="CandidateProfile",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("nom", models.TextField()),
                ("prenom", models.TextField()),
                ("cin", models.TextField(unique=True)),
                ("email", models.TextField()),
                ("telephone", models.TextField()),
                ("ville", models.TextField()),
                ("annee_naissance", models.IntegerField(db_column="anneeNaissance")),
                ("statut", models.CharField(choices=[("EN_ATTENTE", "En attente"), ("VALIDE", "Validé"), ("REJETE", "Rejeté")], default="EN_ATTENTE", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("user", models.OneToOneField(db_column="userId", on_delete=django.db.models.deletion.CASCADE, related_name="candidate_profile", to="users.user")),
            ],
            options={"db_table": "MST_CANDIDATE_PROFILES"},
        ),
        migrations.CreateModel(
            name="LicenceYear",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("annee", models.IntegerField()),
                ("annee_universitaire", models.TextField(db_column="anneeUniversitaire")),
                ("moyenne", models.FloatField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("candidate_profile", models.ForeignKey(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="licence_years", to="candidate_profile.candidateprofile")),
            ],
            options={"db_table": "MST_LICENCE_YEARS"},
        ),
        migrations.CreateModel(
            name="Diplome",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("annee_obtention", models.TextField(db_column="anneeObtention")),
                ("universite", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("candidate_profile", models.OneToOneField(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="diplome", to="candidate_profile.candidateprofile")),
                ("type_licence", models.ForeignKey(db_column="typeLicenceId", on_delete=django.db.models.deletion.PROTECT, related_name="diplomes", to="candidate_profile.typelicence")),
            ],
            options={"db_table": "MST_DIPLOMES"},
        ),
        migrations.CreateModel(
            name="Master1Year",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("annee_universitaire", models.TextField(db_column="anneeUniversitaire")),
                ("moyenne", models.FloatField()),
                ("etablissement", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("candidate_profile", models.OneToOneField(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="master1_year", to="candidate_profile.candidateprofile")),
            ],
            options={"db_table": "MST_MASTER1_YEARS"},
        ),
        migrations.CreateModel(
            name="Redoublement",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("a_redouble", models.BooleanField(db_column="aRedouble", default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("candidate_profile", models.OneToOneField(db_column="candidateProfileId", on_delete=django.db.models.deletion.CASCADE, related_name="redoublement", to="candidate_profile.candidateprofile")),
            ],
            options={"db_table": "MST_REDOUBLEMENTS"},
        ),
        migrations.CreateModel(
            name="RedoublementYear",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("pubkey", models.TextField(unique=True)),
                ("annee", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_column="createdAt")),
                ("updated_at", models.DateTimeField(auto_now=True, db_column="updatedAt")),
                ("deleted_at", models.DateTimeField(blank=True, db_column="deletedAt", null=True)),
                ("redoublement", models.ForeignKey(db_column="redoublementId", on_delete=django.db.models.deletion.CASCADE, related_name="redoublement_years", to="candidate_profile.redoublement")),
            ],
            options={"db_table": "MST_REDOUBLEMENT_YEARS"},
        ),
    ]
