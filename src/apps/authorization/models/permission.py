from django.db import models

from src.shared.models import ManagedModel


class Permission(ManagedModel):
    pubkey = models.TextField(unique=True)
    code = models.TextField(unique=True)
    resource = models.TextField()
    action = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, db_column="createdAt", db_default=models.functions.Now())
    updated_at = models.DateTimeField(null=True, blank=True, db_column="updatedAt")

    class Meta:
        db_table = "AUTH_PERMISSIONS"
