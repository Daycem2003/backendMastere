import time

_CACHE: dict[str, tuple[float, set[str]]] = {}
_TTL_SECONDS = 60


def get_effective_permission_codes(user_pubkey: str) -> set[str]:
    cached = _CACHE.get(user_pubkey)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    codes: set[str] = set()
    from src.apps.authorization.models import UserRole
    assignments = UserRole.objects.select_related("role").prefetch_related("role__role_permissions__permission").filter(user__pubkey=user_pubkey)
    for assignment in assignments:
        codes.update(link.permission.code for link in assignment.role.role_permissions.all())
    _CACHE[user_pubkey] = (time.monotonic() + _TTL_SECONDS, codes)
    return codes


def invalidate_permission_cache(user_pubkey: str) -> None:
    _CACHE.pop(user_pubkey, None)
