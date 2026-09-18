# knowledge_service.py -- answer a question over the knowledge base.
#
# Wraps generation.generate_answer() (retrieve + synthesize + cite) and returns
# a plain result dict the view can serialize. Ollama is a network dependency:
# its failures surface as RuntimeError from deep inside generate_answer(), and
# we translate those into KnowledgeAssistantUnavailableException (HTTP 503) so
# the API contract stays clean. Nothing here touches the DB directly beyond
# what generation/retrieval already do.

from src.apps.knowledge.exceptions.knowledge_exceptions import (
     KnowledgeAssistantUnavailableException,
)
from src.apps.knowledge.generation import (
     Citation,
     GeneratedAnswer,
     generate_answer,
)
from src.apps.knowledge.retrieval import DEFAULT_MIN_SCORE, RetrievedChunk


def _citation_to_dict(c: Citation) -> dict:
     return {
         "n": c.n,
         "source_file": c.source_file,
         "page": c.page,
         "extraction_method": c.extraction_method,
         "score": c.score,
         "excerpt": c.excerpt,
     }


def _context_to_dict(c: RetrievedChunk) -> dict:
     return {
         "rank": c.rank,
         "score": c.score,
         "source_file": c.source_file,
         "page": c.page,
         "extraction_method": c.extraction_method,
         "chunk_pubkey": c.chunk_pubkey,
         "preview": c.preview(300),
     }


def answer_query(
     query: str,
     top_n: int = 5,
     min_score=DEFAULT_MIN_SCORE,
     filename=None,
     **generation_kwargs,
) -> dict:
     """Retrieve + synthesize + cite, returning a JSON-serializable dict.

     `min_score` defaults to the calibrated retrieval floor. A query that
     retrieves no relevant chunks is NOT an error: the answer carries
     `status="no_relevant_context"` with empty citations, which the caller
     surfaces to the user ("the corpus doesn't cover that").

     Raises:
         KnowledgeAssistantUnavailableException -- Ollama unreachable/failed.
     """
     try:
        result = generate_answer(
             query,
             top_n=top_n,
             min_score=min_score,
             filename=filename or None,
             **generation_kwargs,
        )
     except RuntimeError as exc:
        raise KnowledgeAssistantUnavailableException() from exc

     return _render_answer(result)


def _render_answer(result: GeneratedAnswer) -> dict:
     has_context = bool(result.context)
     has_citations = bool(result.citations)

     if not has_context:
        # Retrieval found nothing passing the min-score floor. Do not run a
        # "grounded" flag off an empty pass; report the honest status.
        status = "no_relevant_context"
     elif not has_citations:
        # Context was fed but the model did not cite any passage (it answered
        # from general knowledge or refused). Not grounded.
        status = "answered_ungrounded"
     else:
        status = "answered"

     return {
        "status": status,
        "question": result.query,
        "grounded": result.is_grounded(),
        "answer": result.answer or "",
        "citations": [_citation_to_dict(c) for c in result.citations],
        "context": [_context_to_dict(c) for c in result.context],
        "context_count": len(result.context),
        "model": result.model,
        "deterministic": result.deterministic,
       }
