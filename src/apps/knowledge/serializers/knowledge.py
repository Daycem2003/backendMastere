# serializers/ -- knowledge app request/response serialization.
#
# KnowledgeAskSerializer validates the request body for the /ask endpoint
# (empty-query rejection, max length, bounded top_n, optional min-score
# floor, optional source-file filter). Responses are rendered from the
# service result dict.

from rest_framework import serializers

from src.apps.knowledge.retrieval import DEFAULT_MIN_SCORE, DEFAULT_TOP

# Query length bounds (kept module-level so they read plainly in the contract).
QUERY_MIN_LEN = 3
QUERY_MAX_LEN = 2000
# Bound the chunks handed to the generator so a huge top_n cannot blow the
# prompt / memory on a local 27b model.
TOP_N_MIN = 1
TOP_N_MAX = 10


# Request body for POST /api/v1/knowledge/ask.
#
#   query     : required, non-empty, trimmed, within [QUERY_MIN_LEN, QUERY_MAX_LEN].
#   top_n     : int 1..TOP_N_MAX, default DEFAULT_TOP (chunks fed to the model).
#   min_score : float 0.0..1.0 or null. omitted -> calibrated floor (0.01);
#               explicit null -> opt out of the floor.
#   filename  : optional source-file restriction.
class KnowledgeAskSerializer(serializers.Serializer):
    query = serializers.CharField(
        min_length=QUERY_MIN_LEN,
        max_length=QUERY_MAX_LEN,
        trim_whitespace=True,
        required=True,
    )
    top_n = serializers.IntegerField(
        min_value=TOP_N_MIN,
        max_value=TOP_N_MAX,
        required=False,
        default=DEFAULT_TOP,
    )
    min_score = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        required=False,
        allow_null=True,
        default=DEFAULT_MIN_SCORE,
    )
    filename = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )
