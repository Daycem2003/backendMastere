# retrieval.py -- nearest-neighbour cosine search over ingested knowledge chunks.
#
# Retrieval only (no answer generation): embed a query the SAME way ingestion
# embeds passages (qwen3-embedding:4b via Ollama, Matryoshka-truncate to 1024
# dims, then L2-renormalise), rank the stored chunks by cosine similarity, and
# return the top-N with text, source file, page and score.
#
# The MRL-truncate + renormalise must stay identical to ingest_pdfs.py so the
# query and the corpus share one embedding space.
#
# IMPLEMENTATION NOTE: this small corpus (12 chunks, 4 docs) is scored in
# Python -- we read each stored embedding back through the ORM and dot it with
# the query vector. For a larger corpus, replace the in-Python loop in search()
# with a native pgvector query:
#   SELECT c."text", c."page", c."extractionMethod", d."filename",
#          1 - (c."embedding" <=> %s::vector) AS sim
#   FROM "MST_KINDLEDGE_CHUNKS" c
#   JOIN "MST_KINDLEDGE_DOCUMENTS" d ON d.id = c."documentId"
#   WHERE c."embedding" IS NOT NULL
#   ORDER BY c."embedding" <=> %s::vector LIMIT %s
# backed by an IVFFlat/HNSW index. pgvector (v0.8.6, vector(1024)) is installed.
import json
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

# --- shared constants (mirror ingest_pdfs.py) ---
DEFAULT_MODEL = os.environ.get("KNOWLEDGE_EMBED_MODEL", "qwen3-embedding:4b")
DEFAULT_DIM = int(os.environ.get("KNOWLEDGE_EMBED_DIM", "1024"))
DEFAULT_OLLAMA = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_TOP = int(os.environ.get("KNOWLEDGE_TOP_N", "5"))
# Deterministic embedding: without options Ollama's qwen3-embedding:4b drifts ~4e-4
# (non-deterministic numerics / mlx backend) between calls, so absolute cosine
# scores for the same query wobble run-to-run. Forcing temperature=0 makes the
# /api/embed output bit-exact, which stabilises absolute scores. On by default.
DEFAULT_DETERMINISTIC = os.environ.get("KNOWLEDGE_EMBED_DETERMINISTIC", "1") not in ("0", "false", "no", "")
DEFAULT_SEED = os.environ.get("KNOWLEDGE_EMBED_SEED")  # e.g. "42"; None = none
# Cosine similarity drop-below threshold for retrieval.
# Calibrated on the current corpus (12 chunks / 4 docs): useful matches cluster
# from ~+0.05 down to ~+0.016, with a sharp drop to ~0.00/-0.01 only for the
# truly off-topic chunks. 0.01 keeps every positively-aligned chunk and trims
# just the near-zero/negative noise; tighten (e.g. 0.02-0.025) if a larger
# corpus starts returning too much. Override per-call with --min-score / --no-min-score.
DEFAULT_MIN_SCORE = float(os.environ.get("KNOWLEDGE_MIN_SCORE", "0.01"))


def build_embed_options(deterministic=DEFAULT_DETERMINISTIC, seed=DEFAULT_SEED):
    """Options object sent to Ollama /api/embed.

    temperature=0 (with an optional fixed seed) makes the embedding of a given
    text bit-for-bit reproducible across calls/hosts -- essential so that a
    query and the corpus share one stable embedding space and absolute scores do
    not drift between runs. When deterministic is False we send no options, which
    leaves Ollama at its (slightly non-deterministic) default."""
    if not deterministic:
        return None
    opts = {"temperature": 0.0}
    if seed is not None and seed != "":
        try:
            opts["seed"] = int(seed)
        except ValueError:
            pass
    return opts
DEFAULT_INSTRUCTION = ("Instruct: Given a question about a university master's "
                       "admission process in Arabic or French, retrieve the most "
                       "relevant passage.")


def _renormalize(vec, dim):
    v = [float(x) for x in list(vec)[:dim]]
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def _cosine(a, b, dim):
    a = _renormalize(a, dim)
    b = _renormalize(b, dim)
    return sum(x * y for x, y in zip(a, b))


def _to_float_list(emb, dim):
    """Turn a stored embedding into a list of floats of length <= dim.

    Robust to whatever the DB hands back: a pgvector.Vector object, a numpy
    array, a raw '[...]' string, a Python list/tuple, bytes, or None.
    The non-list shapes are coerced via str(emb) (a pgvector.Vector stringifies
    as '[0.1,0.2,...]') and parsed on comma/whitespace boundaries."""
    if emb is None:
        return None
    if isinstance(emb, (list, tuple)):
        vals = [float(x) for x in emb]
    else:
        s = emb.decode() if isinstance(emb, bytes) else str(emb)
        s = s.strip().strip("[]").strip()
        vals = []
        for piece in s.replace(" ", ",").split(","):
            piece = piece.strip()
            if not piece:
                continue
            try:
                vals.append(float(piece))
            except ValueError:
                continue
    return vals[:dim] if vals else None


def _post_one_embedding(text, model, ollama, attempts=3, options=None):
    body = {"model": model, "input": [text]}
    if options:
        body["options"] = options
    payload = json.dumps(body).encode("utf-8")
    endpoints = [ollama + "/api/embed", ollama + "/api/embeddings"]
    last_err = None
    for _ in range(attempts):
        for ep in endpoints:
            try:
                req = urllib.request.Request(
                      ep, data=payload,
                      headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=300) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if "embeddings" in data:
                    return list(data["embeddings"][0])
                if "embedding" in data:
                    return [data["embedding"]]
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    continue
                last_err = exc
            except Exception as exc:
                last_err = exc
        time.sleep(0.3)
    raise RuntimeError("embedding request failed for text=%r: %s" % (text[:60], last_err))


def embed_query(text, model=DEFAULT_MODEL, dim=DEFAULT_DIM, ollama=DEFAULT_OLLAMA,
                use_instruction=False, task=None, deterministic=DEFAULT_DETERMINISTIC,
                seed=DEFAULT_SEED):
    prompt = text
    if use_instruction:
        instr = task if task is not None else DEFAULT_INSTRUCTION
        prompt = "Instruct: %s\nQuery: %s" % (instr, text)
    raw = _post_one_embedding(prompt, model, ollama,
                              options=build_embed_options(deterministic, seed))
    return _renormalize(raw, dim)


@dataclass
class RetrievedChunk:
    rank: int
    score: float
    text: str
    source_file: str
    page: int
    extraction_method: str
    chunk_pubkey: str = ""

    def preview(self, width=200):
        flat = " ".join(self.text.split())
        return flat[:width] + ("..." if len(flat) > width else "")

    def render(self, width=200):
        flat = " ".join(self.text.split())
        snippet = flat[:width] + ("..." if len(flat) > width else "")
        return ("#%d  sim=%+.4f  p%-2d  [%-26s] (%s)  %s" % (
            self.rank, self.score, self.page, self.source_file[:26],
            self.extraction_method, snippet))


def search(query, top_n=DEFAULT_TOP, min_score=DEFAULT_MIN_SCORE, filename=None,
           model=DEFAULT_MODEL, dim=DEFAULT_DIM, ollama=DEFAULT_OLLAMA,
           use_instruction=False, task=None, deterministic=DEFAULT_DETERMINISTIC,
           seed=DEFAULT_SEED):
    """Rank knowledge chunks by cosine similarity to the query.
    Returns a list of RetrievedChunk, highest score first.
    For a much larger corpus, replace the in-Python ranking loop with a pgvector
    ORDER BY c.embedding <=> %s::vector query plus an IVFFlat index."""
    from django.db import connection
    from pgvector.psycopg2 import register_vector
    from src.apps.knowledge.models import KnowledgeChunk

    # Best effort: register the pgvector adapter so .embedding parses cleanly;
    # _to_float_list also copes with a raw '[...]' string if it does not.
    try:
        connection.ensure_connection()
        register_vector(connection.connection)
    except Exception:
        pass

    q_vec = embed_query(query, model=model, dim=dim, ollama=ollama,
                        use_instruction=use_instruction, task=task,
                        deterministic=deterministic, seed=seed)

    qs = KnowledgeChunk.objects.select_related("document").order_by("document", "page")
    if filename:
        qs = qs.filter(document__filename=filename)

    ranked = []
    for c in qs:
        raw_emb = _to_float_list(c.embedding, dim)
        if not raw_emb:
            continue
        sim = _cosine(q_vec, raw_emb, dim)
        if min_score is not None and sim < min_score:
            continue
        doc = getattr(c, "document", None)
        src = doc.filename if doc is not None else ""
        ranked.append(RetrievedChunk(
              rank=0,
              score=round(sim, 5),
              text=c.text or "",
              source_file=src,
              page=int(c.page) if c.page is not None else 0,
              extraction_method=(c.extraction_method if hasattr(c, "extraction_method") else "text") or "text",
              chunk_pubkey=c.pubkey or "",
         ))
    ranked.sort(key=lambda r: r.score, reverse=True)
    out = ranked[:top_n]
    for i, r in enumerate(out, start=1):
        r.rank = i
    return out
