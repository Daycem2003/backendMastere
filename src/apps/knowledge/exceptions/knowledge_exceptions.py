from rest_framework.exceptions import APIException


class KnowledgeAssistantUnavailableException(APIException):
    """Ollama / the embedding or generation backend is down or unreachable.

    Surfaced as a clean 503 so the client knows to retry later rather than
    treating it as a bad request. The underlying failure is a RuntimeError
    raised deep in generation.generate_answer() / retrieval.search() when the
    Ollama host does not answer.
     """
    status_code = 503
    default_detail = "Service d'assistant indisponible (Ollama)."
