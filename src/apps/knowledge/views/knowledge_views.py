# views/ -- knowledge app HTTP endpoints.
#
# KnowledgeAskView: POST /api/v1/knowledge/ask
#   Request:    { "query", "top_n?", "min_score?", "filename?" }
#   200 -> { status, question, grounded, answer, citations[], context[],
#            context_count, model, deterministic }
#            status in {
#              "answered":              grounded answer with citations
#              "answered_ungrounded":   context fed, model gave no [n] citations
#              "no_relevant_context":   nothing passed the min-score floor
#            }
#   400 -> validation failure (empty / over-long query, out-of-range top_n).
#   401/403 -> unauthenticated.
#   503 -> Ollama unreachable (mapped from the service's domain exception).
#
# Any authenticated user may call it (no PII, but it drives a shared local LLM,
# so we gate behind auth for rate-limiting / abuse control).

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.knowledge.serializers.knowledge import KnowledgeAskSerializer
from src.apps.knowledge.services.knowledge_service import answer_query


class KnowledgeAskView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = KnowledgeAskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = answer_query(
             query=data["query"],
             top_n=int(data.get("top_n", 5)),
             min_score=data.get("min_score"),
             filename=data.get("filename") or None,
             )
        return Response(result, status=status.HTTP_200_OK)
