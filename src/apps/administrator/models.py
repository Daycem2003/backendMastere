from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class Administrateur(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="administrateur", db_column="userId")
    nom = models.TextField()
    email = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = "MST_ADMINISTRATEURS"
