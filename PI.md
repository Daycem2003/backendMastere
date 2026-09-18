# Mastere Backend — Agent Context

Stack: Python 3.11, Django 5.2, DRF, PostgreSQL (pgvector-enabled), Poetry, JWT, pytest

## Environment
- Container runtime: Podman (via podman-compose), NOT Docker Desktop — 
  use `podman-compose` commands, not `docker compose`/`docker-compose`
- Local LLM: Ollama on localhost:11434
  - Generation model: qwen3.8:27b-mlx
  - Embedding model: qwen3-embedding:4b (1024-d, MRL-truncated + renormalized)
- Postgres image: pgvector/pgvector:pg16 (vector extension enabled on app_db)

## Git workflow
- Always work on a feature branch, never commit directly to main
- Current branch: feature/coordinateur-review
- Commit incrementally with clear messages, don't batch everything into one commit
- Show diffs before committing

## Critical rules — do not violate
- NEVER run: migrate, migrate --fake, migrate --fake-initial, prisma migrate, prisma db push
  (only run plain `migrate` with explicit user confirmation, never automatically)
- NEVER recreate, rename, or drop legacy MST_* tables
- MST_* models stay `managed = False` (they're legacy tables)
- AUTH_* tables are the RBAC source of truth — MST_USERS.role is legacy-only, don't use it as an authorization engine
- No binary file content in PostgreSQL — storage uses storage_key references only
- Never log full JWTs, OTPs, or passwords

## Safe verification commands (no DB mutation)
poetry run python manage.py check
poetry run python -m compileall -q src manage.py
poetry run pytest -q
poetry run python manage.py showmigrations

## Feature in progress: coordinateur review
A coordinateur reviews a candidature and either:
- approves it, or
- sends the candidate an email noting a missing document or other issue
Follow the existing documents approve/reject pattern (src/apps/documents) 
where applicable. Coordinateur role/model already exists (coordinator.Coordinateur).

## RAG / AI assistant — status
Building a RAG-based assistant. Stages:
1. Infra (Ollama, Pi, pgvector) — DONE
2. Ingestion (src/apps/knowledge/) — DONE
   - Models: MST_KNOWLEDGE_DOCUMENTS, MST_KNOWLEDGE_CHUNKS (vector(1024) column)
   - Pipeline: PyMuPDF extraction → Arabic-quality gate (odd-codepoint fraction 
     > 0.05 triggers Tesseract OCR ara+eng) → chunk (~800 chars, 160 overlap) → 
     qwen3-embedding:4b → MRL-truncate 2560→1024 + renormalize → pgvector
   - management command: ingest_pdfs (see file for flags)
   - Known caveat: pgvector raw-SQL via Django cursor is broken in this stack 
     (relation not found even on established connection) — retrieval scores in 
     Python instead, documented in retrieval.py. Fine at current corpus size 
     (~12 chunks); revisit if corpus grows large.
3. Retrieval (src/apps/knowledge/retrieval.py, retrieve command) -- DONE
     - embed_query() mirrors ingestion embedding exactly (same model, MRL-truncate+renorm)
     - Cosine similarity search, ORM-based (not raw pgvector SQL, see caveat above)
      - Verified working on French and Arabic test queries
      - DETERMINISTIC: embeddings now default to Ollama options temperature=0 (the default
      path was non-deterministic -- ~4e-4 drift between identical calls). With temperature=0
      the /api/embed output is bit-exact across runs/hosts -> absolute cosine scores are stable.
      Toggle: --no-deterministic or KNOWLEDGE_EMBED_DETERMINISTIC=0. ingest_pdfs.py also embeds
      with temperature=0 now, so corpus + query share one deterministic embedding space.
      - min-score floor: DEFAULT_MIN_SCORE=0.01 (calibrated from the 12-chunk corpus: useful
      matches cluster +0.16..+0.05, off-topic tail is ~0.00/-0.03). 0.01 keeps every
      positively-aligned chunk and trims only near-zero/negative noise. Override per call:
      --min-score N / --no-min-score / KNOWLEDGE_MIN_SCORE. Score values are unchanged by the
      temperature=0 switch -- only their reproducibility improved.
4. GENERATION / SYNTHESIS (src/apps/knowledge/generation.py, `ask` command) -- DONE (CLI only)
      - Pipeline: retrieval.search(top-N) -> prompt qwen3.8:27b-mlx with the query + numbered,
      source-annotated passages -> grounded answer with inline [n] citations. No API endpoint yet.
      - generate_answer() -> GeneratedAnswer{answer, citations[], context[], grounded, prompt,
      raw_output}. A citation = a distinct [n] marker the model actually used, resolved back to
      {source_file, page, extraction_method, score, excerpt}.
      - `ask "query"` prints ANSWER(with [n]) -> CITATIONS USED -> CONTEXT FED -> [grounded: ...].
      Flags: --top, --min-score/--no-min-score, --gen-model, --temperature(default 0.0), --seed,
      --max-tokens, --excerpt, --filename, --no-deterministic, --asymmetric/--instruction, --verbose.
      - Verified on the 3 demo queries (FR: documents requis; FR: date limite+frais;
      AR: الآجال والرسوم). All grounded with per-claim citations; the model honestly reports
      'non mentionne' when the corpus lacks a fact (e.g. the exact fee *amount*).
      - DETERMINISM CAVEAT: embedding temperature=0 is bit-exact, but 27b-mlx GENERATION at
      temperature=0 is only *semantically* reproducible (MLX FP nondeterminism; seed= does not
      fully pin it). Facts + citations are stable run-to-run; wording varies slightly. Fine for CLI.
5. API/integration -- DONE (on `feature/rag-assistant`)
   - Endpoint: `POST /api/v1/knowledge/ask` (mounted in config/urls.py). Thin DRF layer over
     `generation.generate_answer()` -- generation/retrieval untouched. Files: serializers/knowledge.py,
     services/knowledge_service.py, exceptions/knowledge_exceptions.py, views/knowledge_views.py,
     knowledge/urls.py.
   - Serializer: `query` (3..2000 chars, trimmed), `top_n` (1..10, default 5), `min_score`
     (0.0..1.0 or null; omitted -> calibrated floor 0.01; null -> opt out), optional `filename`.
   - Permission: `IsAuthenticated` (confirmed by user -- no PII, but gates the shared LLM for
     rate-limiting). No role restriction. One-line flip to AllowAny if it later goes public.
   - Response: {status, question, grounded, answer, citations[], context[], context_count, model,
     deterministic}. status in {"answered" | "answered_ungrounded" | "no_relevant_context"}.
     Empty/no-context is HTTP 200 (a status field), NOT an error. Ollama down -> HTTP 503
     (KnowledgeAssistantUnavailableException; service maps generation/retrieval RuntimeError->503).
   - VERIFIED LIVE: 200 grounded (FR + AR, per-claim [n] citations, honestly "non mentionne" when
     the corpus lacks a fact); 200 no_relevant_context @ min_score=0.5; 400 empty/over-long/out-of
     range top_n; 401 no auth; 503 @ dead OLLAMA_BASE_URL in ~1s. CAVEAT: one /ask ~= 15-40s
     (local 27b). To test 503, point OLLAMA_BASE_URL at an unused port, do NOT stop real Ollama
     (300s/900s internal timeouts make a down Ollama hang the request, not fast-fail).
6. Frontend UI -- NOT STARTED (out of scope; user said backend-only, "get to it eventually")

Known data quality note: OCR-recovered chunks (from font-garbled/scanned PDFs) have 
some artifacts but are searchable/embeddable — acceptable for RAG, don't over-polish 
unless retrieval quality issues actually show up.

There is a separate frontend repo. Not cloned/explored in depth yet for the RAG feature.
