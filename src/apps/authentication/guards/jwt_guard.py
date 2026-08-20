from rest_framework.permissions import IsAuthenticated


class JwtGuard(IsAuthenticated):
    """DRF access guard; JWT parsing remains in JWTAuthentication."""
