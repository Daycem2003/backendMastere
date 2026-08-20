"""Legacy import path retained during the ORM migration.

Prisma is no longer initialised here. Django owns connection management.
"""

from django.db import connection


def ensure_connection() -> None:
    connection.ensure_connection()
