from django.db import models

from src.shared.models import ManagedModel


class Role(ManagedModel):
    pubkey = models.TextField(unique=True)
    code = models.TextField(unique=True)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    is_system = models.BooleanField(default=False, db_column="isSystem")
    created_at = models.DateTimeField(null=True, blank=True, db_column="createdAt", db_default=models.functions.Now())
    updated_at = models.DateTimeField(null=True, blank=True, db_column="updatedAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        db_table = "AUTH_ROLES"
