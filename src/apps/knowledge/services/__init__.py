# services/ -- knowledge app service layer.
#
# Thin wrappers that isolate the web/serialization layer from the Ollama
# network calls in generation/generation.py and retrieval.py. The view calls
# answer_query(); the service translates a downstream RuntimeError (Ollama
# down / embedding or generation failure) into a domain exception the view can
# map to a clean HTTP 503.
