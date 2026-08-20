DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# TTL du cache en mémoire des permissions effectives par utilisateur
# (voir selectors/authorization_selector.py). Volontairement court : la
# fraîcheur prime sur la performance pour un système d'autorisation.
PERMISSION_CACHE_TTL_SECONDS = 30
