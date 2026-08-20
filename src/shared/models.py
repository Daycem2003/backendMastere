from django.db import models
from django.db.models.expressions import RawSQL


class PostgreSQLEnumField(models.CharField):
    """A Django field backed by an existing PostgreSQL enum type."""

    def __init__(self, *args, enum_name: str, **kwargs):
        self.enum_name = enum_name
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return connection.ops.quote_name(self.enum_name) if connection.vendor == "postgresql" else super().db_type(connection)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum_name"] = self.enum_name
        return name, path, args, kwargs


class ExistingModel(models.Model):
    """Base for Prisma-owned tables: Django may read/write rows, never DDL."""

    id = models.AutoField(primary_key=True)

    class Meta:
        abstract = True
        managed = False


class ManagedModel(models.Model):
    """Base for tables owned by Django migrations."""

    id = models.AutoField(primary_key=True)

    class Meta:
        abstract = True


class TimestampedSoftDeleteModel(ExistingModel):
    created_at = models.DateTimeField(null=True, blank=True, db_column="createdAt", db_default=RawSQL("CURRENT_TIMESTAMP", ()))
    updated_at = models.DateTimeField(null=True, blank=True, db_column="updatedAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        abstract = True
        managed = False


class CreatedSoftDeleteModel(ExistingModel):
    created_at = models.DateTimeField(null=True, blank=True, db_column="createdAt", db_default=RawSQL("CURRENT_TIMESTAMP", ()))
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    class Meta:
        abstract = True
        managed = False
