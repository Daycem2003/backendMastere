from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class Coordinateur(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="coordinateur", db_column="userId")
    nom = models.TextField()
    email = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = "MST_COORDINATEURS"
