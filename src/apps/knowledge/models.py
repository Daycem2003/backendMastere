import math

from django.db import models
from src.shared.models import TimestampedSoftDeleteModel


class VectorField(models.Field):
    """Django field backed by a pgvector vector column.

    Deliberately minimal: declare the column type (db_type), pass a Python
    list of floats / pgvector vector unchanged through get_db_prep_value and
    from_db_value, and deconstruct so migrations serialise dim. The psycopg2
    type adapter that turns a list into the wire vector is registered by the
    ingest_pdfs command via pgvector.psycopg2.register_vector.
    """

    description = "pgvector vector column"

    def __init__(self, dim=1024, **kwargs):
        self.dim = int(dim)
        kwargs.setdefault("null", False)
        kwargs.setdefault("blank", True)
        super().__init__(**kwargs)

    def get_internal_type(self):
        return "FloatField"

    def db_type(self, connection):
        if getattr(connection, "vendor", None) != "postgresql":
            return "text"
        return "vector(%d)" % self.dim

    def get_prep_value(self, value):
        if value is None:
            return None
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        return self.get_prep_value(value)

    def from_db_value(self, value, expression, connection):
        return value

    def to_python(self, value):
        if value is None:
            return None
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["dim"] = self.dim
        return name, path, args, kwargs

    @staticmethod
    def truncate_mrl(vector, dim, renormalize=True):
        """Keep the first dim coordinates then re-normalise (Matryoshka)."""
        prefix = list(vector)[:dim]
        if len(prefix) < dim:
            prefix = prefix + [0.0] * (dim - len(prefix))
        if not renormalize:
            return prefix
        norm = math.sqrt(sum(x * x for x in prefix)) or 1.0
        return [x / norm for x in prefix]


class KnowledgeDocument(TimestampedSoftDeleteModel):
    """One ingested source file."""

    pubkey = models.CharField(max_length=100, unique=True, db_column="pubkey")
    filename = models.CharField(max_length=500, db_column="filename")
    source_path = models.TextField(db_column="sourcePath")
    size_bytes = models.BigIntegerField(default=0, db_column="sizeBytes")
    sha256 = models.CharField(max_length=64, db_index=True, db_column="sha256")
    num_pages = models.PositiveIntegerField(default=0, db_column="numPages")
    status = models.CharField(max_length=20, default="PENDING", db_column="status")
    extraction_summary = models.JSONField(default=dict, db_column="extractionSummary")
    embedding_model = models.CharField(max_length=100, default="", db_column="embeddingModel")
    embedding_dim = models.PositiveIntegerField(default=0, db_column="embeddingDim")
    chunk_count = models.PositiveIntegerField(default=0, db_column="chunkCount")

    class Meta:
        managed = True
        db_table = "MST_KNOWLEDGE_DOCUMENTS"
        ordering = ["filename"]

    def __str__(self):
        return "%s [%s] %d chunks / %dp" % (
            self.filename, self.status, self.chunk_count, self.num_pages
        )


class KnowledgeChunk(TimestampedSoftDeleteModel):
    """One retrievable passage extracted from a KnowledgeDocument."""

    pubkey = models.CharField(max_length=100, unique=True, db_column="pubkey")
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
        db_column="documentId",
    )
    page = models.PositiveIntegerField(db_column="page")
    text = models.TextField(db_column="text")
    char_count = models.IntegerField(default=0, db_column="charCount")
    extraction_method = models.CharField(max_length=10, default="text", db_column="extractionMethod")
    embedding = VectorField(dim=1024, db_column="embedding")

    class Meta:
        managed = True
        db_table = "MST_KNOWLEDGE_CHUNKS"
        ordering = ["document_id", "page"]

    def __str__(self):
        short = (self.pubkey or "?")[:8]
        return "chunk %s doc=%s p%s %s %sc" % (
            short, self.document_id, self.page, self.extraction_method, self.char_count
        )
